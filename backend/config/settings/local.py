from .base import *

DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
