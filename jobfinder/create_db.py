from app import app
from db import db
from models import User, Job

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Create a test user
    test_user = User(
        username='test',
        name='Test User',
        email='test@example.com',
        password='test123'
    )
    db.session.add(test_user)
    db.session.commit()

print("Database created successfully with test user!")



