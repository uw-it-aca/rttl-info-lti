ARG DJANGO_CONTAINER_VERSION=3.0.0

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-container:${DJANGO_CONTAINER_VERSION} AS app-container

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ /app/project/

# Ensure nginx includes directory exists and copy locations.conf
RUN mkdir -p /etc/nginx/includes/
COPY --chown=acait:acait docker/locations.conf /etc/nginx/includes/locations.conf

RUN /app/bin/pip install -r requirements.txt

# Force npm to update internal dependencies and resolve tar version
# Also delete bundled versions and let npm resolve to the new version of tar
# to avoid security vulnerabilities described in CVE-2026-26960
RUN . /app/bin/activate && pip install nodeenv && nodeenv -p && \
    npm install -g npm@11.10.0 && npm update -g && npm install -g tar@7.5.8 --force && \
    ./bin/npm install -g less && \
    rm -rf /app/src && \
    rm -rf /app/lib/node_modules/npm/node_modules/tar

# Clear any existing compressed cache and regenerate static files
RUN rm -rf /app/staticfiles/CACHE
RUN . /app/bin/activate && python manage.py collectstatic --noinput &&\
    python manage.py compress -f

FROM us-docker.pkg.dev/uwit-mci-axdd/containers/django-test-container:${DJANGO_CONTAINER_VERSION} AS app-test-container

COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/
