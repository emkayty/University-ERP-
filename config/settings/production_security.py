"""
Production Settings Additions.
Phase 7 - Security Hardening.
"""

# Security settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Rate limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_CACHE = 'default'
RATELIMIT_DEFAULT = '1000/m'


# 2FA Settings
TOTP_ISSUER_NAME = 'University Portal'


# NDPA Compliance
DATA_RETENTION_PERIODS = {
    'academic_records': 50 * 365,  # 50 years
    'health_records': 10 * 365,     # 10 years
    'financial_records': 7 * 365,   # 7 years
    'biometric_data': 0,             # Delete on graduation
}


# CORS
CORS_ALLOWED_ORIGINS = []
CORS_ALLOW_CREDENTIALS = True