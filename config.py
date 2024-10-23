import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'fresh harvest veggies')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root1989@localhost/fresh_harvest_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
