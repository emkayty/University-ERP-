"""Development settings overrides."""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use SQLite for local development if no PostgreSQL available
if not config("DB_PASSWORD", default=None):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    TENANT_MODEL = None  # Disable tenants in local development without PostgreSQL

# Development-specific settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Disable security middleware in development
MIDDLEWARE = [
    m for m in MIDDLEWARE
    if "SecurityMiddleware" not in m and "XFrameOptionsMiddleware" not in m
]

# More verbose logging in development
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # type: ignore[index]

# Disable Sentry in development
if "sentry_sdk" in globals():
    sentry_sdk.init = lambda **kwargs: None