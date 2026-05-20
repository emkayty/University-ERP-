"""
Minimal settings for generating migrations ONLY.
This does NOT load any base settings to avoid dependency issues.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'test-secret-key-for-migrations-only'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'apps.users',
    'apps.tenants',
    'apps.core',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Minimal AUTH settings
AUTH_USER_MODEL = 'users.User'

# Tenant settings
TENANT_MODEL = 'tenants.University'
TENANT_DOMAIN_MODEL = 'tenants.Domain'

USE_TZ = True