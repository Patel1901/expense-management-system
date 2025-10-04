from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

db = SQLAlchemy()

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='company', lazy=True)
    approval_rules = db.relationship('ApprovalRule', backref='company', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200))
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    manager = db.relationship('User', remote_side=[id], backref='subordinates')
    expenses = db.relationship('Expense', foreign_keys='Expense.employee_id', backref='employee', lazy=True)
    approvals = db.relationship('ExpenseApproval', backref='approver', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_otp(self):
        self.otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.otp_expiry = datetime.utcnow()
        from datetime import timedelta
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        return self.otp_code
    
    def verify_otp(self, otp):
        if self.otp_code == otp and self.otp_expiry and datetime.utcnow() <= self.otp_expiry:
            return True
        return False

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount_in_company_currency = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    receipt_path = db.Column(db.String(200))
    vendor_name = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    current_approval_step = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    final_decision_at = db.Column(db.DateTime)
    
    approvals = db.relationship('ExpenseApproval', backref='expense', lazy=True, cascade='all, delete-orphan')

class ApprovalRule(db.Model):
    __tablename__ = 'approval_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(20), nullable=False)
    percentage_required = db.Column(db.Integer)
    specific_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_manager_first = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    specific_approver = db.relationship('User', foreign_keys=[specific_approver_id])
    approval_steps = db.relationship('ApprovalStep', backref='rule', lazy=True, cascade='all, delete-orphan', order_by='ApprovalStep.sequence')

class ApprovalStep(db.Model):
    __tablename__ = 'approval_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('approval_rules.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    approver = db.relationship('User', foreign_keys=[approver_id])

class ExpenseApproval(db.Model):
    __tablename__ = 'expense_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    step_sequence = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    comments = db.Column(db.Text)
    decision_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
