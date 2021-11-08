.. _introduction_installation:

Installation
============

We ship Kiosc as a Docker container, and provide Docker compose file to start also other required containers.
This part describes how to use Kiosc as a Docker container, and also the manual is based on this.

**Disclaimer:** It is possible to run Kiosc as is (mode ``host``), but this requires additional work to set up the database
and scheduler. This is not described in this manual. Also, this has impact on how the Docker containers the user creates
are organized and presented. This is also not described in this manual.

The Kiosc Docker container is served via Github Container Registry (*gchr*).

Docker compose
--------------

Set up the Docker compose by cloning the repository::

    $ git clone https://github.com/bihealth/kiosc-docker-compose.git
    $ cd kiosc-docker-compose

Initialize the folder structure required. Among others, the database will be stored in there, such it is available
after restarting the container::

    $ bash init.sh

Copy the ``env.example`` file to ``.env``::

    $ cp env.example .env

Here you can change Kiosc and Django parameters. Most of them are set to reasonable defaults, but changing the
``DJANGO_SECRET_KEY`` is a good idea::

    DJANGO_SECRET_KEY=CHANGEMEchangemeCHANGEMEchangemeCHANGEMEchangemeCH

When done, start the Docker containers::

    $ docker-compose up

The Kiosc installation can now be reached by accessing `localhost <https://localhost>`_ with your browser.

Configuration
^^^^^^^^^^^^^

Kiosc can be configured via environment variables. Docker compose can digest a ``.env`` file. It is a good idea to
leave the values as they are.

The environment file could look like this::

    # Postgres configuration ----------------------------------------------------

    POSTGRES_USER=kiosc
    POSTGRES_PASSWORD=password
    POSTGRES_DB=kiosc
    POSTGRES_HOST=postgres

    # Kiosc configuration -------------------------------------------------------

    DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${POSTGRES_DB}"

    DJANGO_ALLOWED_HOSTS="*"
    DJANGO_SECRET_KEY="CHANGEMEchangemeCHANGEMEchangemeCHANGEMEchangemeCH"
    DJANGO_SETTINGS_MODULE="config.settings.production"

    PROJECTROLES_SITE_MODE=SOURCE

    CELERY_BROKER_URL="redis://redis:6379/0"

    KIOSC_SERVER_VERSION=main-0
    KIOSC_NETWORK_MODE=docker-shared
    KIOSC_DOCKER_NETWORK=kiosc-net
    KIOSC_DOCKER_WEB_SERVER=kiosc-web
    kIOSC_DOCKER_ACTION_MIN_DELAY=1
    KIOSC_DOCKER_MAX_INACTIVITY=1
    KIOSC_DOCKER_ACTION_MIN_DELAY=7
    KIOSC_EMBEDDED_FILES=1

Note that setting ``PROJECTROLES_SITE_MODE=TARGET`` requires an upstream SODAR instance
that is running in ``SOURCE`` mode and that the Kiosc instance is registered to.
If no SODAR instance is available or connecting Kiosc to the SODAR instance is not intended,
set the ``PROJECTROLES_SITE_MODE=SOURCE``. Further description of the ``SOURCE``/``TARGET``
mode can be found in the `SODAR Core documentation <https://sodar-core.readthedocs.io/en/latest/app_projectroles_usage.html#remote-projects>`_.

Optionally the LDAP can be configured with up to two LDAP servers::

    # LDAP configuration --------------------------------------------------------

    ENABLE_LDAP=1
    AUTH_LDAP_SERVER_URI=...
    AUTH_LDAP_BIND_PASSWORD=...
    AUTH_LDAP_BIND_DN=...
    AUTH_LDAP_USER_SEARCH_BASE=...
    AUTH_LDAP_USERNAME_DOMAIN=...
    AUTH_LDAP_DOMAIN_PRINTABLE=...

    ENABLE_LDAP_SECONDARY=1
    AUTH_LDAP2_SERVER_URI=...
    AUTH_LDAP2_BIND_PASSWORD=...
    AUTH_LDAP2_BIND_DN=...
    AUTH_LDAP2_USER_SEARCH_BASE=...
    AUTH_LDAP2_USERNAME_DOMAIN=...
    AUTH_LDAP2_DOMAIN_PRINTABLE=...


If the ``KIOSC_`` environment variables are not set, Kiosc selects the defaults as stated
in the following table.

=============================  =============  =========================================================================================================
Environment variable           Default        Description
=============================  =============  =========================================================================================================
KIOSC_NETWORK_MODE             ``host``       Can be ``host`` or ``docker-shared``. Indicates whether installation runs in a Docker environment or not.
KIOSC_DOCKER_NETWORK           ``kiosc-net``  Name of the Docker network for the users Docker containers.
KIOSC_DOCKER_WEB_SERVER        ``kiosc-web``  Name of the web server Docker container.
KIOSC_DOCKER_ACTION_MIN_DELAY  ``1``          Min delay in seconds for Docker container actions.
KIOSC_DOCKER_MAX_INACTIVITY    ``7``          Max threshold for inactive running Docker containers in days.
KIOSC_EMBEDDED_FILES           ``True``       Enable the feature to upload small files to Kiosc that can be served to the Docker containers.
=============================  =============  =========================================================================================================