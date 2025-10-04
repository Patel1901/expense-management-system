from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, Expense, ExpenseApproval, User, ApprovalRule
from datetime import datetime

manager_bp = Blueprint('manager', __name__)

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['manager', 'admin']:
            flash('Manager access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@manager_bp.route('/dashboard')
@login_required
@manager_required
def dashboard():
    pending_approvals = ExpenseApproval.query.filter_by(
        approver_id=current_user.id,
        status='pending'
    ).join(Expense).order_by(Expense.submitted_at.desc()).all()
    
    my_team_expenses = []
    if current_user.role == 'manager':
        my_team_expenses = Expense.query.filter(
            Expense.employee_id.in_([u.id for u in current_user.subordinates])
        ).order_by(Expense.submitted_at.desc()).limit(10).all()
    
    return render_template('manager/dashboard.html', 
                         pending_approvals=pending_approvals,
                         team_expenses=my_team_expenses)

@manager_bp.route('/approvals')
@login_required
@manager_required
def approvals():
    all_approvals = ExpenseApproval.query.filter_by(
        approver_id=current_user.id
    ).join(Expense).order_by(Expense.submitted_at.desc()).all()
    
    return render_template('manager/approvals.html', approvals=all_approvals)

@manager_bp.route('/approvals/<int:approval_id>/review', methods=['GET', 'POST'])
@login_required
@manager_required
def review_approval(approval_id):
    approval = ExpenseApproval.query.get_or_404(approval_id)
    
    if approval.approver_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('manager.dashboard'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comments = request.form.get('comments', '')
        
        approval.status = 'approved' if action == 'approve' else 'rejected'
        approval.comments = comments
        approval.decision_at = datetime.utcnow()
        
        expense = approval.expense
        
        if action == 'reject':
            expense.status = 'rejected'
            expense.final_decision_at = datetime.utcnow()
        else:
            check_and_update_expense_status(expense)
        
        db.session.commit()
        
        flash(f'Expense {action}d successfully', 'success')
        return redirect(url_for('manager.dashboard'))
    
    return render_template('manager/review_approval.html', approval=approval)

@manager_bp.route('/team-expenses')
@login_required
@manager_required
def team_expenses():
    if current_user.role == 'manager':
        team_expenses = Expense.query.filter(
            Expense.employee_id.in_([u.id for u in current_user.subordinates])
        ).order_by(Expense.submitted_at.desc()).all()
    else:
        team_expenses = Expense.query.join(User).filter(
            User.company_id == current_user.company_id
        ).order_by(Expense.submitted_at.desc()).all()
    
    return render_template('manager/team_expenses.html', expenses=team_expenses)

def check_and_update_expense_status(expense):
    active_rule = ApprovalRule.query.filter_by(
        company_id=expense.employee.company_id,
        is_active=True
    ).first()
    
    all_approvals = ExpenseApproval.query.filter_by(expense_id=expense.id).all()
    
    if not active_rule:
        if all(a.status == 'approved' for a in all_approvals):
            expense.status = 'approved'
            expense.final_decision_at = datetime.utcnow()
        return
    
    if active_rule.rule_type == 'percentage':
        approved_count = sum(1 for a in all_approvals if a.status == 'approved')
        total_count = len(all_approvals)
        if total_count > 0:
            approval_percentage = (approved_count / total_count) * 100
            if approval_percentage >= active_rule.percentage_required:
                expense.status = 'approved'
                expense.final_decision_at = datetime.utcnow()
    
    elif active_rule.rule_type == 'specific':
        specific_approval = next(
            (a for a in all_approvals if a.approver_id == active_rule.specific_approver_id),
            None
        )
        if specific_approval and specific_approval.status == 'approved':
            expense.status = 'approved'
            expense.final_decision_at = datetime.utcnow()
    
    elif active_rule.rule_type == 'hybrid':
        approved_count = sum(1 for a in all_approvals if a.status == 'approved')
        total_count = len(all_approvals)
        approval_percentage = (approved_count / total_count) * 100 if total_count > 0 else 0
        
        specific_approval = next(
            (a for a in all_approvals if a.approver_id == active_rule.specific_approver_id),
            None
        )
        
        if (approval_percentage >= active_rule.percentage_required or 
            (specific_approval and specific_approval.status == 'approved')):
            expense.status = 'approved'
            expense.final_decision_at = datetime.utcnow()
    
    elif active_rule.rule_type == 'sequential':
        current_step_approvals = [a for a in all_approvals if a.step_sequence == expense.current_approval_step]
        
        if current_step_approvals and all(a.status == 'approved' for a in current_step_approvals):
            next_step = expense.current_approval_step + 1
            next_step_approvals = [a for a in all_approvals if a.step_sequence == next_step]
            
            if next_step_approvals:
                expense.current_approval_step = next_step
                from utils.email_utils import send_approval_notification
                for approval in next_step_approvals:
                    send_approval_notification(
                        approval.approver.email,
                        expense.id,
                        expense.amount_in_company_currency,
                        expense.employee.company.currency,
                        approval.approver.full_name
                    )
            else:
                expense.status = 'approved'
                expense.final_decision_at = datetime.utcnow()
