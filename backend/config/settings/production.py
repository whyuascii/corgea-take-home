import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
if FIELD_ENCRYPTION_KEY in ("dev-encryption-key-do-not-use-in-production", ""):  # noqa: F405
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY must be set to a strong, unique value in production."
    )

ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production (set the ALLOWED_HOSTS environment variable)")
CORS_ALLOWED_ORIGINS = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
CORS_ALLOW_ALL_ORIGINS = False

SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # frontend JS must read csrftoken for X-CSRFToken header
CSRF_TRUSTED_ORIGINS = [o for o in CORS_ALLOWED_ORIGINS if o]

REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    raise ImproperlyConfigured(
        "REDIS_URL is required in production for distributed rate limiting, "
        "caching, and WebSocket channel layers."
    )

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    }
}
