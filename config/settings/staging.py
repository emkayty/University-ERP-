"""Staging environment settings."""

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = config("STAGING_ALLOWED_HOSTS", default="staging.umis.edu.ng").split(",")

# Force PostgreSQL in staging
assert "sqlite" not in DATABASES["default"].get("ENGINE", ""), "SQLite not allowed in staging"

# CORS settings
CORS_ALLOWED_ORIGINS = config("STAGING_CORS_ORIGINS", default="https://staging.umis.edu.ng").split(",")

# Staging-specific logging
LOGGING["handlers"]["file"]["filename"] = BASE_DIR / "logs" / "staging.log"  # type: ignore[index]

# Reduced traces sampling for staging
if "sentry_sdk" in globals():
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=config("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
        environment="staging",
    )