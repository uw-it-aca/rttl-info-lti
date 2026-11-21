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

## LTI 1.3 Integration

This app is an LTI 1.3 tool built on [django-blti](https://github.com/uw-it-aca/django-blti)
(which wraps pylti1p3). Canvas is the platform; this app never calls Canvas to launch.

### Endpoints (all under `/rttlinfo/`)

| URL | Purpose |
|---|---|
| `blti/login` | OIDC third-party-initiated login: Canvas sends the user here first |
| `blti/jwks` | Tool public key set (Canvas fetches this, e.g. for NRPS/services requests) |
| `/` (`LaunchView`) | Launch / redirect URI: Canvas POSTs the signed `id_token` here |

### Launch flow

1. A user clicks the course navigation link in Canvas. Canvas calls `blti/login` with
   `iss`, `client_id`, `login_hint`, `lti_message_hint`, `lti_deployment_id` and
   `target_link_uri`.
2. django-blti looks up the registration in `tool.json` by issuer (and `client_id`), stores
   state and nonce, and redirects the browser to the platform's `auth_login_url`
   (Canvas `.../api/lti/authorize_redirect`).
3. Canvas authenticates the user and POSTs a signed `id_token` plus `state` to the tool's
   redirect URI (`/rttlinfo/`). The redirect URI must exactly match one of the key's
   Redirect URIs.
4. When the tool runs in an iframe, the browser may not send the session cookie, so
   Canvas advertises client-side storage (`lti_storage_target`). The first POST to
   `/rttlinfo/` is answered with a small JS redirect that fetches state from
   storage and re-POSTs. This first response carries no validated launch. A single
   launch therefore shows up as two requests to `/rttlinfo/` in the logs.
5. django-blti validates the `id_token` signature against the platform's `key_set_url`
   (Canvas JWKS), checks `state`, `nonce` and `deployment_id`, then normalizes the claims
   (course, roles, user) into `self.blti`. `LaunchView` copies that into
   `session['blti_data']` for the rest of the app.

`LTI_CONSUMERS`, `BLTI_AES_KEY`/`BLTI_AES_IV` and LTI 1.1 settings are legacy and not needed
for a 1.3 launch.

### Tool-side configuration (deployed via Helm values)

| Item | Where |
|---|---|
| `tool.json` (platform issuers, `client_id`, `deployment_ids`, platform URLs, key file paths) | `configmaps.lti-tool-config` in `docker/*-values.yml`, mounted at `LTI_CONFIG_DIRECTORY=/lti/config` |
| Tool key pair (`private-key-1.key`, `public-key-1.key`) | ExternalSecret `rttlinfo-lti.rttl.uw.edu-lti-keys`, mounted at `/lti/keys` |
| Other secrets (`DJANGO_SECRET`, `RTTL_API_KEY`, `RTTL_BASE_URL`, `RESTCLIENTS_SWS_OAUTH_BEARER`) | ExternalSecret `rttlinfo-lti.rttl.uw.edu-secrets` |

`tool.json` has one entry per Canvas issuer. Production uses `https://canvas.instructure.com`;
the Canvas test/beta instance uses `https://canvas.test.instructure.com`. Each entry needs
the Developer Key's `client_id` and the installation's `deployment_ids`. A new key pair can be
generated with `python manage.py generate_credentials private.key public.key jwt.json`.

### Canvas configuration (installing the tool)

Registration is manual (django-blti does not implement dynamic registration).
`canvas_app_config_prod.json` is the JSON configuration for the prod key; for another
environment copy it and replace every `jupyter.rttl.uw.edu` host
(`target_link_uri`, `oidc_initiation_url`, `public_jwk_url`, `redirect_uris`, and
`launch_settings.target_link_uri`).

1. **Create the Developer Key** (Admin > Developer Keys > + Developer Key > LTI Key) using
   "Paste JSON" with the file above. Save, then enable the key (state ON).
2. Copy the key's **client ID** (the number in the key's Details column) into the matching
   `client_id` in `tool.json`.
3. **Install the tool** (Settings > Apps > + App > By Client ID) in the account or course
   that should have it, using that client ID.
4. Copy the **deployment ID** from the installed tool's settings (the `Deployment Id` shown
   by the "Copy" action next to the tool) into `deployment_ids` in `tool.json`, then deploy.
5. Check the course navigation. The placement is `default: disabled`, so enable it in the
   course's Settings > Navigation, then launch.

Menu names in Canvas change from time to time; the IDs and URLs above are what matter.

Canvas test/beta refreshes from prod roughly monthly, which overwrites any
changes made there. The refreshed Developer Key keeps the prod URLs, so after each refresh
edit the key in the test instance to use the `jupyter.eval.rttl.uw.edu` URLs.

### Troubleshooting a launch

| Symptom | Likely cause |
|---|---|
| 404 on `/rttlinfo/blti/login` | route not reaching the app; check the gateway HTTPRoute and `/rttlinfo/` path |
| Canvas error before reaching the tool | `client_id` or redirect URI does not match the Developer Key |
| 401 "LTI authentication failure" | `deployment_id` or `client_id` not in `tool.json`, or tool/platform JWKS mismatch |
| Redirect or cookie problems after the first POST | request seen as HTTP; check `X-Forwarded-Scheme` is set to `https` by the HTTPRoute |
| 500 with `'LaunchView' object has no attribute 'blti'` | image predates the launch guard in `LaunchView.dispatch` |

## Running locally with docker compose

Export the RTTL settings first; the app cannot render a launch without `RTTL_API_KEY`:

```bash
export RTTL_API_KEY=<RTTL REST API key>
export RTTL_BASE_URL=https://jupyter.eval.rttl.uw.edu
```

Compose passes these through when set (it also passes `RESTCLIENTS_SWS_DAO_CLASS`, `RESTCLIENTS_SWS_HOST`
and `RESTCLIENTS_SWS_OAUTH_BEARER` if you need SWS data).

| Goal | Command | URL |
|------|---------|-----|
| Deployed-like: gunicorn plus an nginx sidecar | `docker compose up --build` | `http://localhost:8080/rttlinfo/` |
| Mocked LTI launch (runserver, `ENV=localdev`) | `docker compose -f docker-compose.yml -f docker-compose-localdev.yml up --build app` | `http://localhost:8000/rttlinfo/blti/dev` |
| Same, with debugpy on port 5678 | `docker compose -f docker-compose.yml -f docker-compose-debug.yml up --build app` | `http://localhost:8000/rttlinfo/blti/dev` |

The mock launch is only available with `ENV=localdev`, so `/rttlinfo/blti/dev` returns 404 through the
nginx sidecar setup on port 8080.

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

**docker/locations.conf** (also set as `proxyServer.locations` in `docker/*-values.yml`; the app image no longer contains nginx):
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

### Validating LTI launch in eval

The `/rttlinfo/blti/dev` mock launch is intentionally not enabled in deployed
environments (`LTI_DEVELOP_APP` is only set in `docker-compose.yml`): after the first dev
launch it replaces `validate_1p3` for the whole pod process, leaving it in a mocked state.

1. Routing: `curl -sI https://jupyter.eval.rttl.uw.edu/rttlinfo/blti/jwks` should return 200
   with `server: envoy`, and `/rttlinfo/blti/login` should not 404.
2. Real LTI 1.3 launch: launch the tool from the Canvas eval (beta/test) instance.
3. Mocked launches: run locally as described in [Running locally](#running-locally-with-docker-compose).

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