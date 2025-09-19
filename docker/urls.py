from .base_urls import *
from django.conf.urls import include
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns += [
    re_path(r'^rttlinfo/', include('rttlinfo.urls')),
    re_path(r'^rttlinfo/blti/', include('blti.urls')),
]

# Add static files URL pattern for development and fallback
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
