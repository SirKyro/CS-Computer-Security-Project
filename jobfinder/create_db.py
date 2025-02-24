from app import app
from db import db
from models import User, Job
import bcrypt

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Create a test user with bcrypt hash
    test_password = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    test_user = User(
        username='test',
        name='Test User',
        email='test@example.com',
        password=test_password,
        favorite_color='blue',
        role='user'
    )
    
    # Create an admin user with bcrypt hash
    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    admin_user = User(
        username='admin',
        name='Admin User',
        email='admin@example.com',
        password=admin_password,
        favorite_color='red',
        role='admin'
    )
    
    db.session.add(test_user)
    db.session.add(admin_user)
    db.session.commit()

print("Database created successfully with test user and admin user!")



