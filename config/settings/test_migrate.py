# Use base settings but override critical items
from .base import *

# Disable tenants-related apps for migration testing
INSTALLED_APPS = [
    app for app in INSTALLED_APPS 
    if 'tenant' not in app.lower()
]

# Override for testing without database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Simplify middleware
MIDDLEWARE = []

# Use dummy cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}