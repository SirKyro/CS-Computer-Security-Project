class Config:
    SECRET_KEY = 'TestKey'  # Exposed secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True  # Dangerous in production
    PROPAGATE_EXCEPTIONS = True  # Shows detailed error messages
    
    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@gmail.com'  # Replace with your email
    MAIL_PASSWORD = 'your-app-password'     # Replace with app-specific password
