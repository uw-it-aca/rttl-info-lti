from .base_settings import *
import os

INSTALLED_APPS += [
    'rttlinfo.apps.RttlInfoConfig',
    'compressor'
]

COMPRESS_ENABLED = True
COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (('text/less', 'lessc {infile} {outfile}'),)
COMPRESS_OFFLINE = True
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)

COMPRESS_PRECOMPILERS += (
    ('text/x-sass', 'pyscss {infile} > {outfile}'),
    ('text/x-scss', 'pyscss {infile} > {outfile}'),
)

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

DETECT_USER_AGENTS = {
    'is_tablet': False,
    'is_mobile': False,
    'is_desktop': True,
}

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True
else:
    DEBUG = False

RTTL_API_KEY = os.getenv('RTTL_API_KEY', '')
RTTL_BASE_URL = os.getenv('RTTL_BASE_URL')
RESTCLIENTS_SWS_OAUTH_BEARER = os.getenv('RESTCLIENTS_SWS_OAUTH_BEARER', '')
RESTCLIENTS_CA_BUNDLE = os.getenv("RESTCLIENTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
RESTCLIENTS_SWS_DAO_CLASS = os.getenv('RESTCLIENTS_SWS_DAO_CLASS')
RESTCLIENTS_SWS_HOST = os.getenv('RESTCLIENTS_SWS_HOST')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_SCHEME', 'https')

# Trust proxy headers
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# relax samesite requirements, limit casual snooping
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEBUG_LOGGING = os.getenv('DEBUG_LOGGING', 'False')
if DEBUG_LOGGING:
    LOGGING['handlers']['console'] = {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
    }
    LOGGING['loggers']['rttlinfo'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': True,
    }
    LOGGING['loggers']['blti'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    }