# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

"""
Settings overrides used only for running the automated test suite.

Usage:
    manage.py test rttlinfo --settings=project.test_settings
"""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

RTTL_API_KEY = 'test-api-key'
RTTL_BASE_URL = 'https://rttl.example.edu'

# Avoid needing offline compression or lessc to render templates in tests
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False
COMPRESS_PRECOMPILERS = ()

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
