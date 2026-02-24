import sys

from .base import *

# Development status
IS_PRODUCTION = False
DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "project_title",
        "USER": "postgres",
        "PASSWORD": "1234",
        "HOST": "localhost",
        "PORT": "5432",
        "OPTIONS": {
            "pool": {
                "min_size": 5,
                "max_size": 15,
                "max_lifetime": 24 * 60 * 60,
            }
        },
    }
}

# Redis configuration
REDIS_SERVER = "redis://localhost:6379/0"

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
KEY = "ktvI9-rYqmgR8aDNVYqAnZ5ErWAVTj552OIouLEqyzg="
SECRET_KEY = KEY

# External API keys

# Path and URLs
ADMIN_PATH = "admin"
CORE_DOMAIN = "localhost:3210"
CORE_BASE_URL = f"http://{CORE_DOMAIN}"
APP_DOMAIN = "localhost:3230"
APP_BASE_URL = f"http://{APP_DOMAIN}"

# Hosts and origins
HOSTS = ["localhost"]
ALLOWED_HOSTS = ["*"]
ORIGINS = ["http://localhost:3210", "http://localhost:3230"]

# Security configuration
IP_BLOCKEDS = []
SECURITY_MOBILE = "0910XXXXXXX"
ADMIN_LOGIN_MOBILE = "0910XXXXXXX"

# Static files configuration (development)
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = None

# Logging configuration
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Celery broker
CELERY_BROKER_URL = REDIS_SERVER

# CORS configuration
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
