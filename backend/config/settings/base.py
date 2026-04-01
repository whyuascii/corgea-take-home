import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY environment variable is required. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "")
if not FIELD_ENCRYPTION_KEY:
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY environment variable is required for Fernet encryption."
    )
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h]
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 52_428_800  # 50 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000      # cap form-field DoS

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_q",
    "anymail",
    "drf_spectacular",
    "core",
    "accounts",
    "projects",
    "scans",
    "findings",
    "integrations",
]

MIDDLEWARE = [
    "core.middleware.RequestIDMiddleware",
    "core.middleware.BotProtectionMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.ContentTypeValidationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "vulntracker"),
        "USER": os.environ.get("POSTGRES_USER", "vulntracker"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", 600)),
        "CONN_HEALTH_CHECKS": True,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",   # Argon2id — memory-hard, GPU-resistant
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",   # fallback for existing hashes during migration
]

from core.constants import DATA_RETENTION_DAYS, PASSWORD_MIN_LENGTH, Q_TASK_RETRY, Q_TASK_TIMEOUT  # noqa: E402

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
        "login": "5/minute",
        "registration": "3/hour",
        "password_reset": "5/hour",
        "scan_upload": "20/hour",
        "bulk_operation": "30/hour",
        "export": "10/hour",
        "api_key_rotation": "5/hour",
        "integration_test": "20/hour",
        "webhook": "120/minute",
    },
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Dev-only default; overridden by production.py with Redis for multi-worker safety.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]

Q_CLUSTER = {
    "name": "vulntracker",
    "workers": 2,
    "timeout": Q_TASK_TIMEOUT,
    "retry": Q_TASK_RETRY,
    "orm": "default",
    "schedule_broker": True,
}

EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"
ANYMAIL = {
    "RESEND_API_KEY": os.environ.get("RESEND_API_KEY", ""),
}
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "VulnTracker <noreply@vulntracker.dev>")
VULNTRACKER_BASE_URL = os.environ.get("VULNTRACKER_BASE_URL", "http://localhost:3000")

SPECTACULAR_SETTINGS = {
    "TITLE": "VulnTracker API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Security vulnerability tracking and management platform API.",
    "CONTACT": {"name": "VulnTracker", "email": "support@vulntracker.dev"},
    "TAGS": [
        {"name": "Auth", "description": "Authentication and user management"},
        {"name": "Projects", "description": "Project CRUD and membership"},
        {"name": "Scans", "description": "Scan upload, push, and management"},
        {"name": "Findings", "description": "Finding listing, detail, and status management"},
        {"name": "Rules", "description": "Semgrep rule management"},
        {"name": "Overview", "description": "Cross-project overview and analytics"},
        {"name": "Integrations", "description": "Jira/Linear integration config and webhooks"},
        {"name": "Compliance", "description": "SLA tracking and compliance reporting"},
    ],
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAuthenticated"],
}

ASGI_APPLICATION = "config.asgi.application"
# Dev-only default; overridden by production.py with Redis for cross-process messaging.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# Re-export from core.constants so it's accessible via django.conf.settings.
DATA_RETENTION_DAYS = DATA_RETENTION_DAYS  # noqa: F841 — from core.constants import above
