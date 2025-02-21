class Config:
    SECRET_KEY = 'TestKey'  # Used for session management
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # Database URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
