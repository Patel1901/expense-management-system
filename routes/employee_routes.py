from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Expense, ExpenseApproval, ApprovalRule, ApprovalStep
from utils.currency_utils import convert_currency, get_supported_currencies
from utils.ocr_utils import extract_receipt_data
from utils.email_utils import send_approval_notification
from datetime import datetime
import os

employee_bp = Blueprint('employee', __name__)

def allowed_file(filename):
    from config import Config
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@employee_bp.route('/dashboard')
@login_required
def dashboard():
    my_expenses = Expense.query.filter_by(employee_id=current_user.id).order_by(Expense.submitted_at.desc()).all()
    
    pending = sum(1 for e in my_expenses if e.status == 'pending')
    approved = sum(1 for e in my_expenses if e.status == 'approved')
    rejected = sum(1 for e in my_expenses if e.status == 'rejected')
    
    return render_template('employee/dashboard.html', 
                         expenses=my_expenses,
                         pending_count=pending,
                         approved_count=approved,
                         rejected_count=rejected)

@employee_bp.route('/expenses/submit', methods=['GET', 'POST'])
@login_required
def submit_expense():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency')
        category = request.form.get('category')
        description = request.form.get('description')
        expense_date = datetime.strptime(request.form.get('expense_date'), '%Y-%m-%d').date()
        vendor_name = request.form.get('vendor_name', '')
        
        company_currency = current_user.company.currency
        amount_in_company_currency = convert_currency(amount, currency, company_currency)
        
        expense = Expense(
            employee_id=current_user.id,
            amount=amount,
            currency=currency,
            amount_in_company_currency=amount_in_company_currency,
            category=category,
            description=description,
            expense_date=expense_date,
            vendor_name=vendor_name
        )
        
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join('static/uploads/receipts', filename)
                file.save(filepath)
                expense.receipt_path = filepath
        
        db.session.add(expense)
        db.session.flush()
        
        create_approval_workflow(expense)
        
        db.session.commit()
        flash('Expense submitted successfully', 'success')
        return redirect(url_for('employee.dashboard'))
    
    currencies = get_supported_currencies()
    categories = ['Travel', 'Meals', 'Accommodation', 'Transport', 'Supplies', 'Other']
    return render_template('employee/submit_expense.html', currencies=currencies, categories=categories)

@employee_bp.route('/expenses/<int:expense_id>')
@login_required
def view_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if expense.employee_id != current_user.id and current_user.role not in ['admin', 'manager']:
        flash('Access denied', 'error')
        return redirect(url_for('employee.dashboard'))
    
    return render_template('employee/view_expense.html', expense=expense)

@employee_bp.route('/ocr-scan', methods=['POST'])
@login_required
def ocr_scan():
    if 'receipt' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"temp_{current_user.id}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join('static/uploads/receipts', filename)
        file.save(filepath)
        
        extracted_data = extract_receipt_data(filepath)
        
        if extracted_data:
            response_data = {
                'success': True,
                'data': {
                    'amount': extracted_data.get('amount'),
                    'date': extracted_data.get('date').isoformat() if extracted_data.get('date') else None,
                    'vendor': extracted_data.get('vendor'),
                    'description': extracted_data.get('description')
                },
                'filepath': filepath
            }
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'message': 'Failed to extract data from receipt'}), 500
    
    return jsonify({'success': False, 'message': 'Invalid file type'}), 400

def create_approval_workflow(expense):
    active_rule = ApprovalRule.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).first()
    
    if active_rule and active_rule.is_manager_first and current_user.manager:
        approval = ExpenseApproval(
            expense_id=expense.id,
            approver_id=current_user.manager.id,
            step_sequence=0,
            status='pending'
        )
        db.session.add(approval)
        send_approval_notification(
            current_user.manager.email,
            expense.id,
            expense.amount_in_company_currency,
            current_user.company.currency,
            current_user.manager.full_name
        )
    
    if active_rule:
        if active_rule.rule_type == 'sequential':
            for step in active_rule.approval_steps:
                approval = ExpenseApproval(
                    expense_id=expense.id,
                    approver_id=step.approver_id,
                    step_sequence=step.sequence,
                    status='pending'
                )
                db.session.add(approval)
                
                if step.sequence == (1 if active_rule.is_manager_first else 0):
                    send_approval_notification(
                        step.approver.email,
                        expense.id,
                        expense.amount_in_company_currency,
                        current_user.company.currency,
                        step.approver.full_name
                    )
        
        elif active_rule.rule_type == 'percentage':
            for step in active_rule.approval_steps:
                approval = ExpenseApproval(
                    expense_id=expense.id,
                    approver_id=step.approver_id,
                    step_sequence=0,
                    status='pending'
                )
                db.session.add(approval)
                send_approval_notification(
                    step.approver.email,
                    expense.id,
                    expense.amount_in_company_currency,
                    current_user.company.currency,
                    step.approver.full_name
                )
        
        elif active_rule.rule_type == 'specific':
            if active_rule.specific_approver_id:
                approval = ExpenseApproval(
                    expense_id=expense.id,
                    approver_id=active_rule.specific_approver_id,
                    step_sequence=0,
                    status='pending'
                )
                db.session.add(approval)
                send_approval_notification(
                    active_rule.specific_approver.email,
                    expense.id,
                    expense.amount_in_company_currency,
                    current_user.company.currency,
                    active_rule.specific_approver.full_name
                )
        
        elif active_rule.rule_type == 'hybrid':
            for step in active_rule.approval_steps:
                approval = ExpenseApproval(
                    expense_id=expense.id,
                    approver_id=step.approver_id,
                    step_sequence=0,
                    status='pending'
                )
                db.session.add(approval)
                send_approval_notification(
                    step.approver.email,
                    expense.id,
                    expense.amount_in_company_currency,
                    current_user.company.currency,
                    step.approver.full_name
                )
            
            if active_rule.specific_approver_id:
                existing = any(step.approver_id == active_rule.specific_approver_id for step in active_rule.approval_steps)
                if not existing:
                    approval = ExpenseApproval(
                        expense_id=expense.id,
                        approver_id=active_rule.specific_approver_id,
                        step_sequence=0,
                        status='pending'
                    )
                    db.session.add(approval)
                    send_approval_notification(
                        active_rule.specific_approver.email,
                        expense.id,
                        expense.amount_in_company_currency,
                        current_user.company.currency,
                        active_rule.specific_approver.full_name
                    )
