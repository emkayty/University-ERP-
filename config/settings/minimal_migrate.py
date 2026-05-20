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
    'apps.admissions',
    'apps.students',
    'apps.examinations',
    'apps.finance',
    'apps.hr',
    'apps.library',
    'apps.hostel',
    'apps.health',
    'apps.alumni',
    'apps.courses',
    'apps.documents',
    'apps.institutional',
    'apps.timetable',
    'apps.records',
    'apps.nysc',
    'apps.postgraduate',
    'apps.discipline',
    'apps.accreditation',
    'apps.research',
    'apps.performance',
    'apps.hardware',
    'apps.integrations',
    'apps.notifications',
    'apps.access_control',
    'apps.ml',
    'apps.mis',
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