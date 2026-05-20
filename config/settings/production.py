"""Production environment settings - strict security enforcement."""

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = config("PRODUCTION_ALLOWED_HOSTS", default="umis.edu.ng,www.umis.edu.ng").split(",")

# Force PostgreSQL in production
assert "sqlite" in DATABASES["default"].get("ENGINE", ""), "PostgreSQL required in production"

# HTTPS/Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session and cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Content Type Options
SECURE_CONTENT_TYPE_NOSNIFF = True

# Disable browser caching for sensitive data
cache_control_headers = "max-age=0, no-cache, no-store, must-revalidate, proxy-revalidate, private"

# Production CORS - restrictive
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config("PRODUCTION_CORS_ORIGINS", default="https://umis.edu.ng").split(",")

# Production logging
LOGGING["handlers"]["file"]["filename"] = BASE_DIR / "logs" / "production.log"  # type: ignore[index]

# Production Sentry with lower sampling
if "sentry_sdk" in globals():
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=config("SENTRY_DSN"),  # Must be set in production
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.05,  # Lower than staging
        send_default_pii=False,
        environment="production",
    )

# Security headers middleware applied last
MIDDLEWARE = [
    "apps.core.middleware.SecurityHeadersMiddleware",
] + MIDDLEWARE