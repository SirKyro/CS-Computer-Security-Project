from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import User, Job
from instance.config import Config
from db import db

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
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['current_user'] = user.id  # Store user ID in session
            flash("Login successful!")
            return redirect(url_for('main_page'))
        else:
            flash("Invalid login credentials")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists!')
            return redirect(url_for('signup'))

        new_user = User(name=name, email=email, password=password)
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
    session.pop('current_user', None)  # Remove the user from the session
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
    job = Job(title=title, company=company, location=location, description=description, posted_by=user.id)
    db.session.add(job)
    db.session.commit()

    flash('Job posted successfully!')
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist before running
    app.run(debug=True)

