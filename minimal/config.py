import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    TESTING = os.getenv('FLASK_TESTING', 'False').lower() in ['true', '1', 't']
    UPLOAD_FOLDER = './minimal/uploads'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')