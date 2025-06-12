from .base_settings import *
import os

INSTALLED_APPS += [
    'rttlinfo.apps.RttlInfoConfig',
    'compressor'
]

COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (('text/less', 'lessc {infile} {outfile}'),)
COMPRESS_OFFLINE = True
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    RESTCLIENTS_DAO_CACHE_CLASS = 'rttlinfo.cache.RttlHubCache'

RTTL_API_KEY = os.getenv('RTTL_API_KEY', 'FCLZJ0Fo.VTutd8EJWiRruCEcNYB8auEDOW6ZHOus')

# add session authentication based on lauch authentication
# MIDDLEWARE_CLASSES += [
#     'blti.middleware.SessionHeaderMiddleware',
#     'blti.middleware.CSRFHeaderMiddleware',
#     'blti.middleware.SameSiteMiddleware'
#     'blti.middleware.LTISessionAuthenticationMiddleware',]

# relax samesite requirements, limit casual snooping
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_DOMAIN = 'localhost'
SESSION_COOKIE_NAME = 'rttl_sessionid'