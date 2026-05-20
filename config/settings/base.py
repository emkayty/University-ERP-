"""
Django settings for Nigerian University MIS.
Production-grade configuration with django-tenants, PostgreSQL, and NDPA 2023 compliance.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-in-production")

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# =============================================================================
# CUSTOM USER MODEL - MUST BE FIRST BEFORE ANY APP CONFIG
# =============================================================================
AUTH_USER_MODEL = "users.User"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================
INSTALLED_APPS = [
    # Django-tenants must be first
    "django_tenants",
    # Standard Django apps
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    # "django_ninja",  # Disabled for migration - package import issue
    "rest_framework",
    "simple_history",
    "django_fsm",
    "django_filters",
    "corsheaders",
    "storages",
    "channels",
    # Local apps
    "apps.core",
    "apps.users",
    "apps.tenants",
    # Future placeholder apps (uncomment as phases are implemented)
    # "apps.academics",
    # "apps.admissions",
    # "apps.finance",
    # "apps.library",
    # "apps.examinations",
    # "apps.records",
    # "apps.communication",
    # "apps.inventory",
    # "apps.hostel",
    # "apps.transport",
    # "apps.sports",
    # "apps.health",
    # "apps.alumni",
    # "apps.placement",
    # "apps.research",
    # "apps.ict",
    # "apps.specialized",
]

MIDDLEWARE = [
    "django_tenants.middleware.TenantMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Simple history must be last
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# DATABASE - PostgreSQL Only (No SQLite)
# =============================================================================
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME", default="university_mis"),
        "USER": config("DB_USER", default="umis_user"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "OPTIONS": {
            "options": "-c search_path=public"
        },
        "TEST": {
            "NAME": config("TEST_DB_NAME", default="test_university_mis")
        },
    }
}

# Fail loudly if SQLite is attempted
if "sqlite" in DATABASES["default"].get("ENGINE", ""):
    raise ImproperlyConfigured("SQLite is not permitted. Use PostgreSQL.")

# =============================================================================
# TENANT CONFIGURATION
# =============================================================================
TENANT_MODEL = "tenants.University"
TENANT_DOMAIN_MODEL = "tenants.Domain"

SHARED_APPS = [
    "django_tenants",
    "apps.tenants",
    "apps.users",  # Superusers in public schema
]

TENANT_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_ninja",
    "simple_history",
    "django_fsm",
    "django_filters",
    "corsheaders",
    "storages",
    "channels",
    "apps.core",
    # All 18 ERP modules are tenant-specific
    # "apps.academics",
    # "apps.admissions",
    # "apps.finance",
    # "apps.library",
    # "apps.examinations",
    # "apps.records",
    # "apps.communication",
    # "apps.inventory",
    # "apps.hostel",
    # "apps.transport",
    # "apps.sports",
    # "apps.health",
    # "apps.alumni",
    # "apps.placement",
    # "apps.research",
    # "apps.ict",
    # "apps.specialized",
]

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = "en-ng"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================================
# MEDIA FILES
# =============================================================================
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# =============================================================================
# JWT SETTINGS
# =============================================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("ACCESS_TOKEN_LIFETIME_MINUTES", default=30, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SECRET_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Africa/Lagos"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Celery named queues
CELERY_TASK_QUEUES = {
    "default": {"exchange": "default", "routing_key": "default"},
    "payments": {"exchange": "payments", "routing_key": "payments"},
    "jamb": {"exchange": "jamb", "routing_key": "jamb"},
    "notifications": {"exchange": "notifications", "routing_key": "notifications"},
    "documents": {"exchange": "documents", "routing_key": "documents"},
    "ml": {"exchange": "ml", "routing_key": "ml"},
    "infra": {"exchange": "infra", "routing_key": "infra"},
}

# =============================================================================
# CHANNELS (WebSocket)
# =============================================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [config("REDIS_URL", default="redis://localhost:6379/1")],
        },
    }
}

# =============================================================================
# FILE STORAGE (MinIO/S3)
# =============================================================================
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = config("MINIO_BUCKET_NAME", default="umis-files")
AWS_S3_ENDPOINT_URL = config("MINIO_ENDPOINT", default="http://localhost:9000")
AWS_ACCESS_KEY_ID = config("MINIO_ACCESS_KEY", default="")
AWS_SECRET_ACCESS_KEY = config("MINIO_SECRET_KEY", default="")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"
AWS_S3_REGION_NAME = config("AWS_S3_REGION", default="us-east-1")

# =============================================================================
# CORS
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:3000").split(",")
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# SIMPLE HISTORY
# =============================================================================
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_USE_TEXT_FIELD = True
# Use default HistoricalRecords model (auto-created by simple-history)
# Keep default - historical records live in each model's table
# SIMPLE_HISTORY_HISTORY_MODEL = "core.HistoricalRecord"  # Disabled - causes startup error

# =============================================================================
# SENTRY MONITORING
# =============================================================================
SENTRY_DSN = config("SENTRY_DSN", default=None)
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=config("ENVIRONMENT", default="development"),
    )

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================
PROMETHEUS_EXPORT_PORT = config("PROMETHEUS_EXPORT_PORT", default=9090, cast=int)

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@umis.edu.ng")

# =============================================================================
# ANYMAIL (SendGrid)
# =============================================================================
ANYMAIL = {
    "SENDGRID": {
        "API_KEY": config("SENDGRID_API_KEY", default=""),
    }
}

# =============================================================================
# LOGGING
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}