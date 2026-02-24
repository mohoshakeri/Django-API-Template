import sys

from .base import *

# Production status
IS_PRODUCTION = True
DEBUG = False

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASS,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "pool": {
                "min_size": DB_POOL_SIZE,
                "max_size": DB_POOL_SIZE + (DB_POOL_SIZE * 2),
                "max_lifetime": 24 * 60 * 60,
            }
        },
    }
}

# Redis configuration
REDIS_SERVER = os.getenv("REDIS")

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_SERVER,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
    }
}

# Security keys
KEY = os.getenv("KEY")
SECRET_KEY = KEY

# External API keys

# Admin path configuration
ADMIN_PATH = os.getenv("ADMIN_PATH")

CORE_DOMAIN = os.getenv("CORE_DOMAIN")
CORE_BASE_URL = f"https://{CORE_DOMAIN}"
APP_DOMAIN = os.getenv("APP_DOMAIN")
APP_BASE_URL = f"https://{APP_DOMAIN}"

# Hosts and origins
HOSTS = os.getenv("HOSTS").split(",")
ALLOWED_HOSTS = HOSTS
ORIGINS = os.getenv("ORIGINS").split(",")

# Security configuration
IP_BLOCKEDS = (
    os.getenv("IP_BLOCKEDS", "").split(",") if os.getenv("IP_BLOCKEDS", "") else []
)
SECURITY_MOBILE = os.getenv("SECURITY_MOBILE")
ADMIN_LOGIN_MOBILE = os.getenv("ADMIN_LOGIN_MOBILE")

# Static files configuration (production)
STATICFILES_DIRS = []
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Logging configuration
LOG_DIR = "/var/log/project_title"

# Celery broker
CELERY_BROKER_URL = REDIS_SERVER

# CORS and production security configuration
if len(sys.argv) > 1 and sys.argv[1] not in MANAGEMENT_ARGS:
    CORS_ALLOWED_ORIGINS = ORIGINS
    CORS_ALLOW_METHODS = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]

    # Production-specific security settings
    CSRF_TRUSTED_ORIGINS = HOSTS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
