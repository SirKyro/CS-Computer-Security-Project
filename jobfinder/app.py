from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from models import User, Job
from instance.config import Config
from db import db
from datetime import datetime, timedelta
from sqlalchemy import text
import hashlib  # Add this import
import sys
import flask
import socket
from functools import wraps
from flask import abort
import bcrypt
from flask_mail import Mail, Message
import secrets
import time
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)

LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_TIME = 900  # 15 minutes in seconds
SESSION_LIFETIME = 3600  # 1 hour in seconds

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# First, define the decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('main_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    if 'current_user' in session:
        # Check if session has expired
        if 'last_activity' not in session:
            session.clear()
            return redirect(url_for('login'))
            
        last_activity = datetime.fromtimestamp(session['last_activity'])
        if datetime.utcnow() - last_activity > timedelta(seconds=SESSION_LIFETIME):
            session.clear()
            flash('Session expired. Please login again.')
            return redirect(url_for('login'))
            
        # Update last activity
        session['last_activity'] = time.time()

@app.route('/')
@app.route('/main')
@login_required
def main_page():
    try:
        jobs = Job.query.order_by(Job.date_posted.desc()).all()
        user = User.query.get(session['user_id'])
        return render_template('main.html', jobs=jobs, user=user)
    except Exception as e:
        app.logger.error(f'Error in main page: {str(e)}')
        flash('An error occurred while loading the page')
        return render_template('errors/500.html'), 500

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            # Secure query using SQLAlchemy ORM
            user = User.query.filter_by(username=username).first()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                session.clear()
                session['user_id'] = user.id
                session.permanent = True
                flash('Logged in successfully!')
                return redirect(url_for('main_page'))
            else:
                flash('Invalid username or password')
                return redirect(url_for('login'))
                
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            flash('An error occurred during login')
            return redirect(url_for('login'))
            
    return render_template('login.html')

def is_password_strong(password):
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*" for c in password):
        return False
    return True

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def signup():
    if request.method == 'POST':
        try:
            # Check if username or email already exists
            if User.query.filter_by(username=request.form['username']).first():
                flash('Username already exists')
                return redirect(url_for('signup'))
            
            if User.query.filter_by(email=request.form['email']).first():
                flash('Email already registered')
                return redirect(url_for('signup'))
            
            # Hash the password
            hashed_password = bcrypt.hashpw(
                request.form['password'].encode('utf-8'), 
                bcrypt.gensalt()
            )
            
            # Create new user
            new_user = User(
                username=request.form['username'],
                name=request.form['name'],
                email=request.form['email'],
                password=hashed_password.decode('utf-8'),
                role='user'  # Default role
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error in signup: {str(e)}')
            flash('An error occurred during signup. Please try again.')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    user_id = session.get('current_user')
    if user_id:
        # Clear remember me token from database
        user = User.query.get(user_id)
        if user:
            user.remember_token = None
            user.token_expiry = None
            db.session.commit()
    
    # Clear session
    session.clear()
    
    # Clear remember me cookie
    response = make_response(redirect(url_for('login')))
    response.set_cookie('remember_token', '', expires=0, httponly=True, secure=True)
    return response

@app.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    try:
        if request.method == 'POST':
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to post a job')
                return redirect(url_for('login'))

            new_job = Job(
                title=request.form['title'],
                company=request.form['company'],
                location=request.form['location'],
                description=request.form['description'],
                requirements=request.form['requirements'],
                posted_by=user_id,
                date_posted=datetime.utcnow()
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash('Job posted successfully!')
            return redirect(url_for('main_page'))
            
        return render_template('post_job.html')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error posting job: {str(e)}')
        flash('An error occurred while posting the job')
        return redirect(url_for('main_page'))

@app.route('/admin_panel')
@admin_required
def admin_panel():
    users = User.query.all()
    jobs = Job.query.all()
    return render_template('admin.html', users=users, jobs=jobs)

@app.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session['current_user']:
        flash('Cannot delete your own account!')
        return redirect(url_for('admin_panel'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/delete_job/<int:job_id>')
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    # Check if user owns the job or is admin
    user = User.query.get(session['current_user'])
    if job.posted_by != session['current_user'] and user.role != 'admin':
        abort(403)
    
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!')
    return redirect(url_for('main_page'))

@app.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate secure token
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send reset email
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                        sender='noreply@jobfinder.com',
                        recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
The link will expire in 1 hour.
'''
            mail.send(msg)
            flash('Reset instructions sent to your email.')
            return redirect(url_for('login'))
        else:
            flash('Email address not found.')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if user is None or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form['new_password']
        
        # Update password
        user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been updated.')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error but don't show it to the user
    app.logger.error(f'Unhandled exception: {str(e)}')
    return render_template('errors/500.html'), 500

# Remove server header
@app.after_request
def add_security_headers(response):
    response.headers['Server'] = ''
    response.headers['X-Powered-By'] = ''
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com"
    return response

@app.context_processor
def utility_processor():
    def get_user():
        if 'user_id' in session:
            return User.query.get(session['user_id'])
        return None
    return dict(user=get_user())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist before running
    app.run(debug=True)

