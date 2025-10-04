from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Company, ApprovalRule, ApprovalStep, Expense
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    company = current_user.company
    total_employees = User.query.filter_by(company_id=company.id).count()
    total_expenses = Expense.query.join(User).filter(User.company_id == company.id).count()
    pending_expenses = Expense.query.join(User).filter(
        User.company_id == company.id,
        Expense.status == 'pending'
    ).count()
    
    recent_expenses = Expense.query.join(User).filter(
        User.company_id == company.id
    ).order_by(Expense.submitted_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         total_employees=total_employees,
                         total_expenses=total_expenses,
                         pending_expenses=pending_expenses,
                         recent_expenses=recent_expenses)

@admin_bp.route('/employees')
@login_required
@admin_required
def employees():
    company_employees = User.query.filter_by(company_id=current_user.company_id).all()
    return render_template('admin/employees.html', employees=company_employees)

@admin_bp.route('/employees/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_employee():
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        password = request.form.get('password')
        manager_id = request.form.get('manager_id')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin.create_employee'))
        
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            company_id=current_user.company_id,
            manager_id=int(manager_id) if manager_id else None,
            is_verified=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'{role.capitalize()} created successfully', 'success')
        return redirect(url_for('admin.employees'))
    
    managers = User.query.filter_by(company_id=current_user.company_id, role='manager').all()
    return render_template('admin/create_employee.html', managers=managers)

@admin_bp.route('/employees/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_employee(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.company_id != current_user.company_id:
        flash('Access denied', 'error')
        return redirect(url_for('admin.employees'))
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.role = request.form.get('role')
        manager_id = request.form.get('manager_id')
        user.manager_id = int(manager_id) if manager_id else None
        
        password = request.form.get('password')
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('Employee updated successfully', 'success')
        return redirect(url_for('admin.employees'))
    
    managers = User.query.filter(
        User.company_id == current_user.company_id,
        User.role == 'manager',
        User.id != user_id
    ).all()
    return render_template('admin/edit_employee.html', user=user, managers=managers)

@admin_bp.route('/approval-rules')
@login_required
@admin_required
def approval_rules():
    rules = ApprovalRule.query.filter_by(company_id=current_user.company_id).all()
    return render_template('admin/approval_rules.html', rules=rules)

@admin_bp.route('/approval-rules/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_approval_rule():
    if request.method == 'POST':
        name = request.form.get('name')
        rule_type = request.form.get('rule_type')
        is_manager_first = request.form.get('is_manager_first') == 'on'
        percentage_required = request.form.get('percentage_required')
        specific_approver_id = request.form.get('specific_approver_id')
        approver_ids = request.form.getlist('approver_ids[]')
        
        rule = ApprovalRule(
            company_id=current_user.company_id,
            name=name,
            rule_type=rule_type,
            is_manager_first=is_manager_first,
            percentage_required=int(percentage_required) if percentage_required else None,
            specific_approver_id=int(specific_approver_id) if specific_approver_id else None
        )
        
        db.session.add(rule)
        db.session.flush()
        
        for idx, approver_id in enumerate(approver_ids):
            if approver_id:
                step = ApprovalStep(
                    rule_id=rule.id,
                    approver_id=int(approver_id),
                    sequence=idx + 1
                )
                db.session.add(step)
        
        db.session.commit()
        flash('Approval rule created successfully', 'success')
        return redirect(url_for('admin.approval_rules'))
    
    approvers = User.query.filter(
        User.company_id == current_user.company_id,
        User.role.in_(['manager', 'admin'])
    ).all()
    return render_template('admin/create_approval_rule.html', approvers=approvers)

@admin_bp.route('/expenses')
@login_required
@admin_required
def all_expenses():
    expenses = Expense.query.join(User).filter(
        User.company_id == current_user.company_id
    ).order_by(Expense.submitted_at.desc()).all()
    return render_template('admin/all_expenses.html', expenses=expenses)
