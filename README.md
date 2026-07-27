# UW RTTL Info LTI App

[![Build Status](https://github.com/uw-it-aca/rttl-info-lti/workflows/Build%2C%20Test%20and%20Deploy/badge.svg?branch=main)](https://github.com/uw-it-aca/rttl-info-lti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/rttl-info-lti/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/rttl-info-lti?branch=main)

An LTI tool for request and status on RTTL course resources.

Project settings.py
------------------

**INSTALLED_APPS**

    'rttlinfo',
    'blti',

**REST client app settings**

    RTTL_API_KEY = 'Valid_RTTL_REST API key'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    Assuming the ingress URL is `https://example.com/rttlinfo/`
    re_path(r'^rttlinfo/', include('rttlinfo.urls')),
    re_path(r'^rttlinfo/blti/', include('blti.urls')),

## Deployment Notes

### Static Files Configuration

This application is deployed in Kubernetes with an ingress that only routes `/rttlinfo/` paths to the service.

#### Key Configuration:

**docker/settings.py:**
```python
STATIC_ROOT = '/static'           # Where Django collects files (base container default)
STATIC_URL = '/rttlinfo/static/'  # URL prefix for static files
COMPRESS_ROOT = STATIC_ROOT       # Where compressor looks for files
COMPRESS_URL = STATIC_URL         # URL prefix for compressed files
```

**docker/locations.conf:**
```nginx
location /rttlinfo/static/ {
    alias /static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

#### Static Files Flow:

1. **Build time**: 
   - `collectstatic` puts files in `/static/` (base container behavior)
   - `compress` creates compressed files with URLs like `/rttlinfo/static/CACHE/css/output.xxx.css`

2. **Runtime**:
   - Browser requests `/rttlinfo/static/CACHE/css/output.xxx.css`
   - Kubernetes ingress routes to service (matches `/rttlinfo/` prefix)
   - nginx serves from `/static/CACHE/css/output.xxx.css`

#### Kubernetes Ingress:
```yaml
- path: /rttlinfo/
  pathType: Prefix
```

#### Important Notes:
- The base Django container sets `STATIC_ROOT = '/static'` by default
- Always clear compressed cache when changing static URL configuration: `RUN rm -rf /static/CACHE`
- Django Compressor requires `COMPRESS_URL` to match `STATIC_URL` for proper URL generation

### Deployment Commands

```bash
# Build and push new image
make docker-push

# Show available make targets
make help
```

### Troubleshooting

#### Static Files Not Loading
1. Check that `STATIC_URL = '/rttlinfo/static/'` in docker/settings.py
2. Verify nginx locations.conf has correct alias path
3. Ensure Docker build clears old compressed cache
4. Check Kubernetes ingress routing

#### Compress Errors
If you see "isn't accessible via COMPRESS_URL" errors:
1. Verify `COMPRESS_ROOT` matches where files are collected
2. Ensure `COMPRESS_URL` matches `STATIC_URL`
3. Clear compressed cache and rebuild