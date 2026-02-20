.. _introduction_installation:

Installation
============

The easiest way to start using Kiosc is through Docker. We
provide a docker-compose file (in a `separate repository
<https://github.com/bihealth/kiosc-docker-compose>`__) which contains everything
you need for deploying and/or developing Kiosc. This chapter describes how to
use Kiosc with our docker-compose, and the rest of the manual assumes that you
are using this method. If you want to contribute to the development of Kiosc,
the :ref:`Development Environment <introduction_development>` chapter shows you how
to prepare a development environment.

The Kiosc Docker container is build from the `kiosc-server
<https://github.com/bihealth/kiosc-server>`__ repository and is served via
Github Container Registry (*gchr*).

Docker compose
--------------

Set up the Docker compose by cloning the repository::

    $ git clone https://github.com/bihealth/kiosc-docker-compose.git
    $ cd kiosc-docker-compose

First, initialize the required folder structure. Among others, the database will
be stored in there, so that it is available after restarting the container::

    $ bash init.sh

Copy the ``env.example`` file to ``.env``::

    $ cp env.example .env

Here you can change various settings which affect Django, Kiosc, and SODAR
Core. Most of them are set to reasonable defaults, but please go through them
and change them to values that work in your setup. For example, changing the
``DJANGO_SECRET_KEY`` is a good idea::

    DJANGO_SECRET_KEY=CHANGEMEchangemeCHANGEMEchangemeCHANGEMEchangemeCH

See ":ref:`introduction_installation_configuration`" below for a detailed
description of the main options. When done, start the Docker containers::

    $ docker compose --profile=deploy up

The Kiosc installation can now be reached by accessing `localhost
<https://localhost>`_ with your browser.


.. _introduction_installation_configuration:

Configuration
-------------

Kiosc can be configured via environment variables. The Kiosc container running
in our docker compose reads the environment variables from the ``.env`` file,
which is preconfigured for running a demo instance, but you'll need to make some
tweaks to adapt it to your specific requirements.

Here is a description of the most important options.

``NETWORK_BRIDGE_NAME``
    Name of the network where the Kiosc web server will run.

``KIOSC_SERVER_VERSION``
    Version tag for the Kiosc docker image.

``REDIS_VERSION``
    Version tag for the redis docker image.

``TRAEFIK_VERSION``
    Version tag for the traefik docker image.

``KIOSC_DATABASE_URL``
    URL of the database used by Kiosc (do not change this unless you know what
    you are doing).

``KIOSC_DJANGO_ALLOWED_HOSTS``
    Hosts from which connections are accepted.

``KIOSC_DJANGO_SECRET_KEY``
    Used to secure signed data, please change the value and never share it with
    anyone.

``KIOSC_DJANGO_SETTINGS_MODULE``
    Settings module used for the Kiosc Django site.

``KIOSC_EMBEDDED_FILES``
    Enable the feature to upload small files to Kiosc that can be served to the
    Docker containers.

``KIOSC_CELERY_BROKER_URL``
    Used by Celery for keeping track of background tasks.

``KIOSC_UVICORN_WORKERS``
    Number of processes used to handle incoming connections by the web server.

``KIOSC_ENABLE_LDAP``
    Whether to enable LDAP authentication.

``KIOSC_ENABLE_LDAP_SECONDARY``
    Whether to enable the secondary LDAP server for authentication.

``KIOSC_ENABLE_OIDC``
    Whether to enable OIDC authentication.

``KIOSC_AXES_ENABLED``
    Used to enable django-axes, which logs failed login attempts and prevents
    brute-force attacks.

``KIOSC_SITE_TITLE``
    The title of your website.

``KIOSC_SITE_SUBTITLE``
    The subtitle of your website.

``KIOSC_SITE_INSTANCE_TITLE``
    May be used to e.g. differentiate between site versions used for deployment
    or staging, use in different organizations, etc.

``KIOSC_LOGGING_LEVEL``
    Logging level used througout Kiosc apps.

``KIOSC_LOGGING_FILE_PATH``
    Logging file used througout Kiosc apps.


.. note::

    The list of settings for projectroles and the other SODAR Core apps
    is not exhaustive. Consult the SODAR Core documentation to find out more:
    https://sodar-core.readthedocs.io/en/latest/app_projectroles_settings.html


Additionally, there are some environment variables which affect specifically the
Kiosc apps (as opposed to the whole website). These should also be set in the
``.env`` file and are described in the following table.

=============================  =================  =========================================================================================================
Environment variable           Default            Description
=============================  =================  =========================================================================================================
KIOSC_NETWORK_MODE             ``docker-shared``  Can be ``host`` or ``docker-shared``. Indicates whether installation runs in a Docker environment or not.
KIOSC_DOCKER_NETWORK           ``kiosc-net``      Name of the Docker network for the users Docker containers.
KIOSC_DOCKER_WEB_SERVER        ``kiosc-web``      Name of the web server Docker container.
KIOSC_DOCKER_ACTION_MIN_DELAY  ``1``              Min delay in seconds for Docker container actions.
KIOSC_DOCKER_MAX_INACTIVITY    ``7``              Max threshold for inactive running Docker containers in days.
KIOSC_EMBEDDED_FILES           ``True``           Enable the feature to upload small files to Kiosc that can be served to the Docker containers.
=============================  =================  =========================================================================================================


Creating a SODAR site in TARGET mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kiosc can be run in ``TARGET`` mode, drawing projects and users from
an upstream SODAR instance. Note that this requires an existing
SODAR instance which is running in ``SOURCE`` mode and that the
Kiosc instance is registered to it. Further description of the
``SOURCE``/``TARGET`` mode can be found in the `SODAR Core documentation
<https://sodar-core.readthedocs.io/en/latest/app_projectroles_usage.html#remote-projects>`_.

To enable ``TARGET`` mode in your site, set ``PROJECTROLES_SITE_MODE=TARGET``
and add the following environment variables, changing their value as needed::

    # Allow creation of local projects
    PROJECTROLES_TARGET_CREATE=1
    # Enable synchronization with the source site
    PROJECTROLES_TARGET_SYNC_ENABLE=1
    # Time interval in minutes for synchronization
    PROJECTROLES_TARGET_SYNC_INTERVAL=5
