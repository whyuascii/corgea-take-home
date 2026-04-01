import os

# Set dev defaults BEFORE importing base (base.py requires them).
os.environ.setdefault("DJANGO_SECRET_KEY", "dev-secret-key-do-not-use-in-production")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "dev-encryption-key-do-not-use-in-production")

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = False  # incompatible with CORS_ALLOW_CREDENTIALS

# Use console email backend in development (no Resend key needed)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
