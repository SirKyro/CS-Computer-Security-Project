from flask import Flask, render_template, request, redirect, url_for, flash, session
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

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail = Mail(app)

@app.route('/')
def home():
    if session.get('current_user'):
        return redirect(url_for('main_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
            session['current_user'] = user.id
            flash("Login successful!")
            return redirect(url_for('main_page'))
        else:
            flash("Invalid login credentials")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username']
            name = request.form['name']
            email = request.form['email']
            password = bcrypt.hashpw(
                request.form['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            favorite_color = request.form['favorite_color']

            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists!')
                return redirect(url_for('signup'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists!')
                return redirect(url_for('signup'))

            new_user = User(
                username=username,
                name=name,
                email=email,
                password=password,
                favorite_color=favorite_color,
                role='user'
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Account created successfully!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    if not session.get('current_user'):
        return redirect(url_for('login'))

    user = User.query.get(session['current_user'])  # Retrieve the user
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        description = request.form['description']
        
        job = Job(title=title, company=company, location=location, description=description, posted_by=user.id)
        db.session.add(job)
        db.session.commit()
        
        flash('Job posted successfully!')
        return redirect(url_for('main_page'))

    jobs = Job.query.all()  # Get all jobs from the database
    return render_template('main.html', jobs=jobs)

@app.route('/logout')
def logout():
    # Vulnerable: Doesn't invalidate on server side
    session.pop('current_user', None)
    return redirect(url_for('login'))

@app.route('/post_job')
def post_job_page():
    if not session.get('current_user'):
        return redirect(url_for('login'))
    return render_template('post_job.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    if not session.get('current_user'):
        return redirect(url_for('login'))

    title = request.form['title']
    company = request.form['company']
    location = request.form['location']
    description = request.form['description']

    user = User.query.get(session['current_user'])
    job = Job(
        title=title,
        company=company,
        location=location,
        description=description,
        posted_by=user.email,
        date_posted=datetime.utcnow()
    )
    db.session.add(job)
    db.session.commit()

    flash('Job posted successfully!')
    return redirect(url_for('main_page'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'current_user' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'current_user' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        
        user = User.query.get(session['current_user'])
        if not user or user.role != 'admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

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

@app.errorhandler(Exception)
def handle_error(error):
    # Vulnerable: Exposes sensitive information in error messages
    error_info = {
        'error_type': str(type(error).__name__),
        'error_message': str(error),
        'python_version': sys.version,
        'flask_version': flask.__version__,
        'sql_uri': app.config['SQLALCHEMY_DATABASE_URI'],
        'debug_mode': app.config['DEBUG'],
        'server_name': socket.gethostname()
    }
    return render_template('error.html', error_info=error_info), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist before running
    app.run(debug=True)

