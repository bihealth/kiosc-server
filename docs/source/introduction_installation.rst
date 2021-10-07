.. _introduction_installation:

Installation
============

In the ``config/settings/base.py`` file, the following
properties are set that can be set by setting the
corresponding environment variable.

=============================  =============  =========================================================================================================
Environment variable           Default        Description
=============================  =============  =========================================================================================================
KIOSC_NETWORK_MODE             ``host``       Can be ``host`` or ``docker-shared``. Indicates whether installation runs in a Docker environment or not.
KIOSC_DOCKER_NETWORK           ``kiosc-net``  Name of the Docker network for the users Docker containers.
KIOSC_DOCKER_WEB_SERVER        ``kiosc-web``  Name of the web server Docker container.
KIOSC_DOCKER_ACTION_MIN_DELAY  ``1``          Min delay in seconds for Docker container actions.
KIOSC_DOCKER_MAX_INACTIVITY    ``7``          Max threshold for inactive running Docker containers in days.
=============================  =============  =========================================================================================================