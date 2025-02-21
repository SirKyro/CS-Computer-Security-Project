from app import db
from models import User  # Import your models here

# Create the database and tables
db.create_all()

print("Database created successfully!")
