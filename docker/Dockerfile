FROM python:3.8-buster

MAINTAINER Oliver Stolpe <oliver.stolpe@bih-charite.de>
LABEL org.opencontainers.image.source https://github.com/bihealth/kiosc-server

ARG app_git_url=https://github.com/bihealth/kiosc-server.git
ARG app_git_tag
ARG app_git_depth=1

ENV DEBIAN_FRONTEND noninteractive
ENV CUSTOM_STATIC_DIR /usr/src/app/local-static
# As long as we serve from internal cubi-gitlab via SSH.
ENV GIT_SSH_COMMAND "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

## Add the wait script to the image
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /usr/local/bin/wait
RUN chmod +x /usr/local/bin/wait

# Copy source code into Docker image.
RUN mkdir -p /usr/src
RUN git clone --depth $app_git_depth --branch $app_git_tag $app_git_url /usr/src/app

# Install system dependencies.
RUN apt-get update && \
    apt-get install -y \
        apt-utils \
        gcc \
        ldap-utils \
        libldap2-dev \
        libsasl2-dev \
        make \
        postgresql-client \
        wget

# Install Python dependencies.
RUN cd /usr/src/app && \
    pip install --use-deprecated=legacy-resolver --no-cache-dir -r requirements/production.txt && \
    pip install --use-deprecated=legacy-resolver --no-cache-dir -r requirements/local.txt && \
    pip install --use-deprecated=legacy-resolver --no-cache-dir -r requirements/ldap.txt && \
    pip install --use-deprecated=legacy-resolver celery  # appears to be missing

# Download files from CDN.
RUN mkdir -p /usr/src/app/local-static/local/css && \
    mkdir -p /usr/src/app/local-static/local/fonts && \
    mkdir -p /usr/src/app/local-static/local/js && \
    cd /usr/src/app/local-static/local/fonts && \
    wget \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/FontAwesome.otf \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.eot \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.svg \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.ttf \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.woff \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts/fontawesome-webfont.woff2 && \
    \
    cd /usr/src/app/local-static/local/css && \
    wget \
        https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css && \
    \
    cd /usr/src/app/local-static/local/js && \
    wget \
        https://code.jquery.com/jquery-3.5.1.min.js \
        https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js \
        https://cdnjs.cloudflare.com/ajax/libs/tether/1.4.4/js/tether.js \
        https://cdnjs.cloudflare.com/ajax/libs/shepherd/1.8.1/js/shepherd.min.js \
        https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.0/clipboard.min.js

# Get icons
RUN cd /usr/src/app && \
    DJANGO_SECRET_KEY=for-build-only \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DATABASE_URL=postgres://kiosc:kiosc@fake/kiosc \
    python manage.py geticons -c octicon eos-icons

# Prepare static files
RUN cd /usr/src/app && \
    DJANGO_SECRET_KEY=for-build-only \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DATABASE_URL=postgres://kiosc:kiosc@fake/kiosc \
    python manage.py collectstatic --no-input

# Define the entry point.
COPY docker-entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["asgi"]
EXPOSE 8080/tcp
