# encoding: utf-8
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Basic configues settings"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    API_KEY: str = os.getenv('API_KEY')

    # Configs for connecting to MySQL
    # SQLALCHEMY_DATABASE_URI - mysql's format: 'dialect+driver://username:password@host:port/database'
    # SQLALCHEMY_DATABASE_URI - sqlite's format: 'sqlite:///cafes.db'
    DIALECT = "mysql"
    DRIVER = "mysqldb"
    USERNAME: str = os.getenv('USERNAME')
    PASSWORD: str = os.getenv('PASSWORD')
    HOST: str = os.getenv('HOST')
    PORT: str = os.getenv('PORT')
    DATABASE: str = os.getenv('DATABASE')
    SQLALCHEMY_DATABASE_URI = f"{DIALECT}+{DRIVER}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configs for E-mail:
    MAIL_SERVER: str = os.getenv('MAIL_SERVER')
    MAIL_PORT: int = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    OWN_EMAIL: str = os.getenv('OWN_EMAIL')
    OWN_PW :str = os.getenv('OWN_PW')


class DevelopmentConfig(Config):
    """Development Config settings"""
    DEBUG = True


class ProductionConfig(Config):
    """Production Configs Settings"""
    DEBUG = False

conf = DevelopmentConfig