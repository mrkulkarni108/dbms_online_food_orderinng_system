import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / '.env'
load_dotenv(ENV_FILE)


class BaseConfig:
    """Shared runtime settings for every environment."""

    BASE_DIR = BASE_DIR
    SQL_DIR = BASE_DIR / 'backend' / 'sql'
    LOG_DIR = BASE_DIR / 'logs'

    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'change-this-in-production')
    APP_ENV = os.getenv('APP_ENV', 'development').lower()
    DEBUG = False
    TESTING = False

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'food_delivery')
    DB_POOL_NAME = os.getenv('DB_POOL_NAME', 'food_delivery_pool')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_LIFETIME_HOURS', '8')))

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    SESSION_COOKIE_SECURE = True


CONFIG_BY_NAME = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}


def get_config():
    return CONFIG_BY_NAME.get(os.getenv('APP_ENV', 'development').lower(), DevelopmentConfig)
