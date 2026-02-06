FROM ubuntu:noble

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

WORKDIR /usr/src/app

LABEL org.opencontainers.image.authors="Oliver Stolpe <oliver.stolpe@bih-charite.de>"
LABEL org.opencontainers.image.source=https://github.com/bihealth/kiosc-server


## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.1/wait /usr/local/bin/wait
RUN chmod +x /usr/local/bin/wait

# Copy the project files.
COPY . .

# Install system dependencies.
RUN utility/install_os_dependencies.sh
RUN utility/install_postgres.sh
RUN utility/install_redis.sh
RUN utility/install_ldap_dependencies.sh
RUN utility/install_python.sh

# Install extra system utilities
RUN apt-get install -y \
        apt-utils \
        postgresql-client \
        wget

RUN apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# Create Python virtual environment (KIOSC dependencies conflict with
# the system packages).
RUN python3.13 -m venv /venv
ENV PATH=/venv/bin:$PATH

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements/production.txt && \
    pip install --no-cache-dir -r requirements/local.txt && \
    pip install --no-cache-dir -r requirements/ldap.txt

# Download files from CDN.
RUN mkdir -p local-static/local/css && \
    mkdir -p local-static/local/fonts && \
    mkdir -p local-static/local/js && \
    wget -P local-static/local/fonts \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/FontAwesome.otf \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.eot \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.svg \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.ttf \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.woff \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.woff2 \
    && \
    wget -P local-static/local/css \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css.map \
    && \
    wget -P local-static/local/js \
        https://code.jquery.com/jquery-3.5.1.min.js \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js.map \
        https://cdnjs.cloudflare.com/ajax/libs/tether/1.4.4/js/tether.js \
        https://cdnjs.cloudflare.com/ajax/libs/shepherd/1.8.1/js/shepherd.min.js \
        https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.0/clipboard.min.js

# Get icons
RUN DJANGO_SECRET_KEY=for-build-only \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DATABASE_URL=postgres://kiosc:kiosc@fake/kiosc \
    python manage.py geticons -c octicon eos-icons

# Prepare static files
RUN DJANGO_SECRET_KEY=for-build-only \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DATABASE_URL=postgres://kiosc:kiosc@fake/kiosc \
    python manage.py collectstatic --no-input

# Define the entry point.

COPY docker/docker-entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["asgi"]
EXPOSE 8080/tcp
