from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from models import db, User, Company
from utils.email_utils import send_otp_email
from utils.currency_utils import get_all_countries_currencies
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        company_name = request.form.get('company_name')
        country = request.form.get('country')
        currency = request.form.get('currency')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup'))
        
        company = Company(name=company_name, country=country, currency=currency)
        db.session.add(company)
        db.session.flush()
        
        user = User(
            email=email,
            full_name=full_name,
            role='admin',
            company_id=company.id
        )
        user.set_password(password)
        otp = user.generate_otp()
        
        db.session.add(user)
        db.session.commit()
        
        send_otp_email(email, otp, full_name)
        
        session['pending_verification_user_id'] = user.id
        flash('OTP sent to your email. Please verify to complete registration.', 'success')
        return redirect(url_for('auth.verify_otp'))
    
    countries_currencies = get_all_countries_currencies()
    return render_template('auth/signup.html', countries_currencies=countries_currencies)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('pending_verification_user_id')
    if not user_id:
        flash('Please sign up first', 'error')
        return redirect(url_for('auth.signup'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.signup'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        
        if user.verify_otp(otp):
            user.is_verified = True
            user.otp_code = None
            user.otp_expiry = None
            db.session.commit()
            
            next_page = session.pop('login_next_page', None)
            session.pop('pending_verification_user_id', None)
            login_user(user)
            flash('Login successful! Welcome to Expense Manager.', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid or expired OTP', 'error')
    
    return render_template('auth/verify_otp.html', email=user.email)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            otp = user.generate_otp()
            db.session.commit()
            send_otp_email(email, otp, user.full_name)
            session['pending_verification_user_id'] = user.id
            session['login_next_page'] = request.args.get('next')
            flash('OTP sent to your email. Please verify to login.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_id = session.get('pending_verification_user_id')
    if not user_id:
        return {'success': False, 'message': 'No pending verification'}, 400
    
    user = User.query.get(user_id)
    if not user:
        return {'success': False, 'message': 'User not found'}, 404
    
    otp = user.generate_otp()
    db.session.commit()
    
    if send_otp_email(user.email, otp, user.full_name):
        return {'success': True, 'message': 'OTP resent successfully'}
    else:
        return {'success': False, 'message': 'Failed to send OTP'}, 500
