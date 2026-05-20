# Use base settings but override critical items
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# Disable tenants for testing - simplified settings
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'simple_history',
    'django_fsm',
    'django_filters',
    'corsheaders',
    'storages',
    'apps.users',
    'apps.core',
    'apps.students',
    'apps.admissions',
    'apps.finance',
    'apps.hr',
    'apps.examinations',
]

# Override for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MIDDLEWARE = []

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable tenant routing for tests
TENANT_MODEL = None
TENANT_DOMAIN_MODEL = None

AUTH_USER_MODEL = 'users.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'