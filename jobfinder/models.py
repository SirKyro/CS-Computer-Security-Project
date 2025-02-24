from db import db  # Import db from db.py

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Increased length for bcrypt hash
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    favorite_color = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.username}>'

class Job(db.Model):  # This defines a "job" table
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)  
    date_posted = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'



