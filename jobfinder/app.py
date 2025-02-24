from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import User, Job
from instance.config import Config
from db import db
from datetime import datetime
from sqlalchemy import text
import hashlib  # Add this import

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def home():
    if session.get('current_user'):
        return redirect(url_for('main_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # Hash the input password for comparison
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        # Vulnerable SQL query with hashed password
        query = text(f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'")
        result = db.session.execute(query)
        user = result.fetchone()

        if user:
            # Vulnerable: No session timeout set
            session['current_user'] = user[0]  # Just stores user ID without any expiration
            # Vulnerable: No session regeneration
            # Vulnerable: No remember-me token
            flash("Login successful!")
            return redirect(url_for('main_page'))
        else:
            # Vulnerable: No login attempt counting
            flash("Invalid login credentials")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()
        favorite_color = request.form['favorite_color']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('signup'))

        new_user = User(
            username=username, 
            name=name, 
            email=email, 
            password=password,
            favorite_color=favorite_color
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!')
        return redirect(url_for('login'))
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

@app.route('/delete_job/<int:job_id>', methods=['GET'])
def delete_job(job_id):
    # Vulnerable: No authentication check!
    job = Job.query.get(job_id)
    if job:
        db.session.delete(job)
        db.session.commit()
        flash('Job deleted successfully!')
    return redirect(url_for('main_page'))

@app.route('/admin_panel')
def admin_panel():
    # Vulnerable: No admin check!
    users = User.query.all()
    jobs = Job.query.all()
    return render_template('admin.html', users=users, jobs=jobs)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    # Vulnerable: No authentication check!
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!')
    return redirect(url_for('admin_panel'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        
        if user:
            session['reset_user'] = user.username
            return redirect(url_for('security_question'))
        else:
            flash('Username not found')
            
    return render_template('forgot_password.html')

@app.route('/security_question', methods=['GET', 'POST'])
def security_question():
    if 'reset_user' not in session:
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        color = request.form['color']
        user = User.query.filter_by(username=session['reset_user']).first()
        
        if user and color == user.favorite_color:
            return redirect(url_for('reset_password'))
        else:
            flash('Incorrect answer')
            
    return render_template('security_question.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user' not in session:
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        new_password = request.form['new_password']
        user = User.query.filter_by(username=session['reset_user']).first()
        
        if user:
            user.password = hashlib.md5(new_password.encode()).hexdigest()
            db.session.commit()
            session.pop('reset_user', None)
            flash('Password reset successful!')
            return redirect(url_for('login'))
            
    return render_template('reset_password.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist before running
    app.run(debug=True)

