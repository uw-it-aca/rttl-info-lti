from .base_settings import *

INSTALLED_APPS += [
    'rttlinfo.apps.RttlInfoConfig',
    'compressor',
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
