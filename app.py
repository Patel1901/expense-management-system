from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from config import Config
from models import db, User
from utils.email_utils import mail
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.employee_routes import employee_bp
from routes.manager_routes import manager_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(manager_bp, url_prefix='/manager')

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'manager':
            return redirect(url_for('manager.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def not_found(e):
    return render_template('shared/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('shared/500.html'), 500

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=8000)
