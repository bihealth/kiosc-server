.. _introduction_installation:

Installation and configuration
==============================

The code for Kiosc is hosted on `GitHub
<https://github.com/bihealth/kiosc-server>`__. Kiosc itself is a Python web
app built using the `Django <https://www.djangoproject.com>`__ framework and
in order to function properly it requires additional components. Thus, the
easiest and most recommended way to install Kiosc is through Docker Compose. If
you are not familiar with Docker or Docker Compose, head to :ref:`this short
guide <introduction_docker>` for a quick introduction. If you don't want to
use Docker Compose, or if you want to contribute to the Kiosc development, the
manual installation method is described in the :ref:`Development Environment
<introduction_development>` section.

Installation via Docker Compose
-------------------------------

We provide a `separate repository
<https://github.com/bihealth/kiosc-docker-compose>`__ containing the master
``docker-compose.yml`` file for Kiosc. It encloses all the apps and services
needed to deploy and develop Kiosc. We crafted this Docker Compose so that
it uses the latest stable Kiosc image, which is itself built from the main
`kiosc-server repository <https://github.com/bihealth/kiosc-server>`__ and
uploaded to the GitHub Container Registry (*ghcr*). Here we describe how to
deploying Kiosc using the ``kiosc-docker-compose`` repository.

Start by cloning the repository::

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

Before you can access Kiosc, you need to create at least one superuser.
To do so, run this command and follow the interactive prompts::

    $ docker compose exec kiosc-web ./manage.py createsuperuser

At this point, you may create local user accounts or connect Kiosc to
an existing authentication provider, such as LDAP or OIDC. See the
:ref:`introduction_installation_configuration` section for further instructions.

The Kiosc installation can now be reached by accessing https://localhost
with your browser. You should be able to access with the superuser account you
just created, or as any of the regular users, if you have set them up.


.. _introduction_installation_usage:

First steps
-----------

Create a "Hello World" project with a toy app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Running the following command in the terminal will create a top-level category,
create a project within that category, and set up a demo of a `Shiny app
<https://rocker-project.org/images/versioned/shiny.html>`__. You can use this
app as a smoke test for the success of the installation.

::

    docker compose exec -it kiosc-web ./manage.py createtoyapp

Manually create a top-level category
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Kiosc, every project must belong to a category. Only the superuser is allowed
to create and add members to top-level categories, while regular users can
create projects inside categories where they are owners. To create a category,
click on the "Create Category" button in the left menu. Afterwards, you'll be
able to modify the members of the category or create subprojects within it,
again from the left-side menu. When you are inside a project, you will see
additional entries in the left-side menu; clicking on the "Containers" button
will bring you to a list view of the current containers in the project, from
where you can also create new ones.

Set up local user accounts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Kiosc supports centralized authentication methods, including LDAP and SSO (check
out the :ref:`introduction_installation_configuration` instructions). However,
if you are setting up a small and local installation for your colleagues, you
may simply want to create a few local accounts. If you are comfortable with the
command line, this can be done by running the following command::

    docker compose exec -it kiosc-web ./manage.py shell -c 'User.objects.create_user("<username>", "<email>", "<password>")'

Where you should replace the fields within ``<angle brackets>`` with the
relevant values.

Creating user accounts can also be done from the admin web interface: navigate
to https://localhost/admin/users and click "Add".

Using the web interface
^^^^^^^^^^^^^^^^^^^^^^^

The best way to learn Kiosc is by exploring the web interface. Check
out the `manual <https://kiosc-server.readthedocs.io/en/latest/>`__ for
detailed iformation about all the components. If you get stuck, recall
that Kiosc is a `Django <https://www.djangoproject.com>`__ site based on
the `SODAR-Core <https://github.com/bihealth/sodar-core>`__ framework,
so you can often find help on the dedicated support channels for these
projects. For Kiosc-specific problems, please use the `issue tracker
<https://github.com/bihealth/kiosc-server/issues>`__ or contact the authors
directly.


.. _introduction_installation_configuration:

Configuration
-------------

Kiosc can be configured via environment variables. The Kiosc container running
in our Docker Compose reads the environment variables from the ``.env`` file,
which is preconfigured for running a demo instance. If you just want to test the
installation, the default values will suffice. For a production configuration,
you'll need to make some tweaks to adapt it to your specific requirements. At
the very least, you should change the following variables:

- ``KIOSC_DJANGO_SECRET_KEY``: set it to a randomly generated string
- ``KIOSC_UVICORN_WORKERS``: set it to the number of CPUs on your machine (or
  fewer)
- ``KIOSC_ADMINS``: set the admin real name and email address
- ``KIOSC_PROJECTROLES_DEFAULT_ADMIN``: set it to the username of the superuser
  you created after the installation

Here is a description of all relevant options in the same order as they appear
in the ``.env`` file, with their default value.

.. rubric:: Docker Compose configuration

``NETWORK_BRIDGE_NAME=br-kiosc-public``
    Name of the network where the Kiosc web server will run. This should not be
    changed.

.. rubric:: Image versions

``KIOSC_SERVER_VERSION=v0.5.2-0``
    Version tag for the Kiosc Docker image. It can be safely updated to a higher
    patch number within the same minor version. Increasing the minor version is
    not recommended as it could be break things. The Docker Compose file is
    kept in sync with the Kiosc version.

``REDIS_VERSION=8``
    Version tag for the Redis Docker image.

``TRAEFIK_VERSION=v3``
    Version tag for the Traefik Docker image.


.. rubric:: Kiosc configuration

``KIOSC_DATABASE_URL="postgresql://kiosc:kiosc@postgres/kiosc"``
    URL of the database used by Kiosc (do not change this unless you know what
    you are doing).

``KIOSC_DJANGO_ALLOWED_HOSTS="*"``
    Hosts from which connections are accepted.

``KIOSC_DJANGO_SECRET_KEY=CHANGEMEchangemeCHANGEMEchangemeCHANGEMEchangemeCH``
    Used to secure signed data, please change the value and never share it with
    anyone.

``KIOSC_DJANGO_SETTINGS_MODULE="config.settings.production"``
    Settings module used for the Kiosc Django site. In a development
    environment, change this to "config.settings.local". If you are experienced
    with Django, you may even want to create your own module.

``KIOSC_DOCKER_ACTION_MIN_DELAY=1``
    Minimum delay in seconds between consecutive Docker container actions.

``KIOSC_DOCKER_MAX_INACTIVITY=5``
    Maximum threshold for inactive running Docker containers in days.

``KIOSC_DOCKER_NETWORK=kiosc-net``
    Name of the Docker network for the user-created Docker containers. This
    should not be changed.

``KIOSC_DOCKER_WEB_SERVER=kiosc-web``
    Name of the web server Docker container. This must match the name of the
    corresponding service in the Docker compose file, so don't change it
    unless you know what you are doing.

``KIOSC_EMBEDDED_FILES=1``
    Enable the feature to upload small files to Kiosc that can be served to the
    Docker containers.

``KIOSC_NETWORK_MODE=docker-shared``
    Can be ``host`` or ``docker-shared``. Indicates whether installation runs
    in a Docker environment or not. When using Kiosc from the Docker compose in
    "deploy" mode, it should be ``docker-shared``. Only when running Kiosc in
    development mode should it be ``host``.

``KIOSC_CELERY_BROKER_URL="redis://redis:6379/0"``
    Database used by Celery for keeping track of background tasks. Do not change
    this unless you know what you are doing.

``KIOSC_UVICORN_WORKERS=16``
    Number of processes used to handle incoming connections by the web server.


.. rubric:: Kiosc LDAP auth

See `django-auth-ldap documentation
<https://django-auth-ldap.readthedocs.io/en/latest/reference.html#settings>`_
for detailed documentation on specific settings directly derived from that
package.

``KIOSC_ENABLE_LDAP=0``
    Whether to enable LDAP authentication; all other options do not have effect
    unless this variable is set to 1.

``KIOSC_LDAP_DEBUG=0``
    Whether to enable debugging for LDAP.

``KIOSC_AUTH_LDAP_SERVER_URI=``
    The URI of the LDAP server.

``KIOSC_AUTH_LDAP_BIND_PASSWORD=``
    Bind password for authentication to the LDAP server.

``KIOSC_AUTH_LDAP_BIND_DN=``
    Bind distinguished name for authentication to the LDAP server (*i.e.,*, the
    path of the account used to authenticate).

``KIOSC_AUTH_LDAP_USER_SEARCH_BASE=``
    The base DN where all searches for user accounts start.

``KIOSC_AUTH_LDAP_USERNAME_DOMAIN=``
    The domain for which authentication requests are handled by this LDAP server.

``KIOSC_AUTH_LDAP_DOMAIN_PRINTABLE=``
    Human-readable name for the LDAP username domain.

``KIOSC_AUTH_LDAP_START_TLS=``
    Path to the start-TLS certificate to encrypt the connection. This may not be
    needed the LDAP server uses the ``ldaps`` protocol.

``KIOSC_AUTH_LDAP_CA_CERT_FILE=``
    Path to the certificate file to verify the authenticity of the LDAP server.

``KIOSC_AUTH_LDAP_USER_FILTER=``
    LDAP filter applied to all user search requests.

``KIOSC_ENABLE_LDAP_SECONDARY=0``
    Whether to enable LDAP authentication for a second server; all subsequent
    options do not have effect unless this variable is set to 1.

``KIOSC_AUTH_LDAP2_SERVER_URI=``
    The URI of the secondary LDAP server.

``KIOSC_AUTH_LDAP2_BIND_PASSWORD=``
    Bind password for authentication to the secondary LDAP server.

``KIOSC_AUTH_LDAP2_BIND_DN=``
    Bind distinguished name for authentication to the secondary LDAP server
    (*i.e.,*, the path of the account used to authenticate).

``KIOSC_AUTH_LDAP2_USER_SEARCH_BASE=``
    The base DN where all searches for user accounts start.

``KIOSC_AUTH_LDAP2_USERNAME_DOMAIN=``
    The domain for which authentication requests are handled by this secondary
    LDAP server.

``KIOSC_AUTH_LDAP2_DOMAIN_PRINTABLE=``
    Human-readable name for the secondary LDAP username domain.

``KIOSC_AUTH_LDAP2_START_TLS=``
    Path to the start-TLS certificate to encrypt the connection. This may not be
    needed the secondary LDAP server uses the ``ldaps`` protocol.

``KIOSC_AUTH_LDAP2_CA_CERT_FILE=``
    Path to the certificate file to verify the authenticity of the secondary LDAP server.

``KIOSC_AUTH_LDAP2_USER_FILTER=``
    LDAP filter applied to all user search requests.


.. rubric:: Kiosc OIDC auth


OIDC support is implemented using the ``social_django`` app. You first need to
add the app to your ``INSTALLED_APPS``:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'social_django',  # For OIDC authentication
    ]

Next, you must add the app's URL patterns in ``config/urls.py``:

.. code-block:: python

    urlpatterns = [
        # ...
        # Social auth for OIDC support
        path('social/', include('social_django.urls')),
    ]

Finally, check out ``config/settings/base.py`` and modify the OIDC part, if
needed. You can also configure the behaviour through the following variables.

``KIOSC_ENABLE_OIDC=0``
    Whether to enable OIDC authentication.

``KIOSC_SOCIAL_AUTH_OIDC_OIDC_ENDPOINT=``
    Endpoint URL for the OIDC provider. The configuration file
    ``.well-known/openid-configuration`` is expected to be found under this URL.

``SOCIAL_AUTH_OIDC_KEY=``
    Your client ID in the OIDC provider.

``SOCIAL_AUTH_OIDC_SECRET=``
    Secret for the OIDC provider.

``SOCIAL_AUTH_OIDC_USERNAME_KEY=``
    If the username key of the browser is expected to be something other than
    the default ``username``, it can be configured here. The values in this must
    be unique and should preferably be human readable. If the OIDC provider does
    not return such a username directly, it is possible to e.g. use the user
    email as a unique user name.


.. rubric:: Django-Axes configuration

``django-axes`` logs failed login attempts and prevents brute-force attacks. To
enable it, you first need to add the ``axes`` app, middleware and authentication
backend to relevant settings in ``config/settings/base.py``. Note that the
ordering matters in certain settings:

.. code-block:: python

    THIRD_PARTY_APPS = [
        # ...
        'axes',  # Django-axes for login security
    ]
    MIDDLEWARE = [
        # ...
        'axes.middleware.AxesMiddleware',  # Should be the last one on the list
    ]
    AUTHENTICATION_BACKENDS = [
        # NOTE: AxesBackend must be the first backend in the list
        'axes.backends.AxesBackend',
        # ...
    ]

For more information on using and configuring Axes, see the
`django-axes documentation <https://django-axes.readthedocs.io/>`_.
You can change the axis settings through the following environment variables.


``KIOSC_AXES_ENABLED=0``
    Used to enable django-axes.

``KIOSC_AXES_COOLOFF_TIME=``
    Cooloff time for failure lock-out in hours (integer).

``KIOSC_AXES_DISABLE_CLIENT_IP_STORAGE=1``
    Disable storing IP addresses for GDPR compliance if True (boolean).
    **NOTE:** Not a built-in Axes setting but a SODAR Core specific workaround,
    see ``config/settings/base.py`` in this repo for an example of its use.

``KIOSC_AXES_FAILURE_LIMIT=5``
    Number of login attempts allowed before a record is created for failed
    logins (integer).

``KIOSC_AXES_LOCK_OUT_AT_FAILURE=0``
    Lock out user at failure if True (boolean).

``KIOSC_AXES_LOCKOUT_PARAMETERS=username``
    Lockout parameters. by default, block by username only for GRPR compliance
    (list)

``KIOSC_AXES_ONLY_ADMIN_SITE=0``
    Only enable lock for admin site if True (boolean).


.. rubric:: Email settings

``KIOSC_ADMINALERTS_EMAIL_SENDING_DEFAULT=1``
    Set alert email sending default in alert form (boolean).

``KIOSC_PROJECTROLES_EMAIL_SENDER_REPLY=0``
    Whether replies are expected to the sender address (bool). If set ``False``
    and nothing is set in the ``reply-to`` header, a "do not reply" note is
    added to the email body.

``KIOSC_PROJECTROLES_SEND_EMAIL=0``
    Enable/disable email sending (bool)

``KIOSC_SODAR_EMAIL_SENDER=``
    Sender address to be displayed in sent email (string)

``KIOSC_SODAR_EMAIL_SUBJECT_PREFIX=``
    Prefix to be displayed in the subject line of sent email (string)

``KIOSC_SODAR_EMAIL_URL=``
    URL of the email server along with its protocol, user and password. Email
    server authentication settings will be derived from this URL (string)


.. rubric:: Kiosc site settings

``KIOSC_SITE_TITLE="KIOSC"``
    The title of your website.

``KIOSC_SITE_SUBTITLE="Beta"``
    The subtitle of your website.

``KIOSC_SITE_INSTANCE_TITLE="Acme Kiosc"``
    May be used to e.g. differentiate between site versions used for deployment
    or staging, use in different organizations, etc.

``KIOSC_ADMINS="First Admin:admin@example.com,Second Admin:admin2@example.com"``
    Name and email of the site administrators.


.. rubric:: Kiosc logging settings

``KIOSC_LOGGING_LEVEL=ERROR``
    Logging level used througout Kiosc apps.

``KIOSC_LOGGING_FILE_PATH=``
    Logging file used througout Kiosc apps.


.. rubric:: Kiosc REST API settings

``KIOSC_PROJECTROLES_API_USER_DETAIL_RESTRICT=0``
    If true, restrict projectroles API user list and detail view results
    to users who have roles in at least one category or project. For
    ``UserListAPIView`` this will be restricted to contributor access or above.
    ``UserRetrieveAPIView`` is accessible to users with any role (bool).

``KIOSC_TOKENS_CREATE_PROJECT_USER_RESTRICT=0``
    Restrict access to token creation for users with project roles (bool).


.. rubric:: Other Kiosc SODAR Core settings

``KIOSC_PROJECTROLES_ALLOW_ANONYMOUS=0``
    If true, allow anonymous users to access the site and all projects where
    public_access is set to a role (bool).

``KIOSC_PROJECTROLES_ALLOW_LOCAL_USERS=1``
    If true, roles for local non-LDAP users can be synchronized from a source
    during remote project sync if they exist on the target site. Similarly,
    local users will be selectable in member dropdowns when selecting users
    (bool).

``KIOSC_PROJECTROLES_CUSTOM_CSS_INCLUDES=``
    List of custom CSS includes to supplement the existing ones. These can
    either be local static file paths or web URLs to e.g. CDN served files.

``KIOSC_PROJECTROLES_CUSTOM_JS_INCLUDES=``
    List of custom CSS includes to supplement the existing ones. These can
    either be local static file paths or web URLs to e.g. CDN served files.

``KIOSC_PROJECTROLES_DEFAULT_ADMIN=admin``
    User name of the default superuser account used in e.g. replacing an
    unavailable user or performing backend admin commands (string).

``KIOSC_PROJECTROLES_DELEGATE_LIMIT=1``
    The number of delegate roles allowed per project. The amount is limited to
    1 per project if not set, unlimited if set to 0. Will be ignored for remote
    projects synchronized from a source site (int).

``KIOSC_PROJECTROLES_DISABLE_CDN_INCLUDES=0``
    If using the default CDN imports for JQuery, Bootstrap4 etc. are not an
    optimal solution in your use case due to e.g. network issues, you can
    disable these includes by setting PROJECTROLES_DISABLE_CDN_INCLUDES to True.
    In this case, you MUST provide replacements for all disabled files in your
    custom includes. Otherwise your SODAR Core based site will not function
    correctly!

``KIOSC_PROJECTROLES_INLINE_HEAD_INCLUDE=``
    HTML string to be included in the ``head`` tag of every page in the site.

``KIOSC_PROJECTROLES_READ_ONLY_MSG="This site is currently in read-only mode. Modifying data is not permitted."``
    Custom message to be displayed if site read-only mode is enabled (string)

``KIOSC_PROJECTROLES_SITE_MODE=SOURCE``
    Either "SOURCE" or "TARGET". If "SOURCE", the site stands alone and does not
    depend on an upstream SODAR instance. If "TARGET", projects and users are
    synchronized from an upstream SODAR site.

``KIOSC_PROJECTROLES_SUPPORT_CONTACT=``
    Support contact to be displayed for users, overrides ADMINS. Input as
    "name:email" (string).

``KIOSC_PROJECTROLES_TARGET_CREATE=1``
    Enable or disable project creation if site is in TARGET mode. . If your site
    is in SOURCE mode, this setting has no effect.

``KIOSC_PROJECTROLES_TARGET_SYNC_ENABLE=1``
    Enable/disable remote project synchronization as a target site. Ignored for
    source sites (bool).

``KIOSC_PROJECTROLES_TARGET_SYNC_INTERVAL=5``
    Interval in minutes for remote project synchronization as a target site.
    Ignored for source sites (int).


.. note::

    The list of settings for projectroles and the other SODAR Core
    apps is not exhaustive. Consult the `SODAR Core documentation
    <https://sodar-core.readthedocs.io/en/latest/app_projectroles_settings.html>`__
    to find out more.


Configuring authentication may require a special set up, since
it will be highly dependent on the environment where Kiosc
is hosted. Local users can be created from the Django admin
page or with the ``manage.py`` script (see the `Django docs
<https://docs.djangoproject.com/en/5.2/topics/auth/default/>`__). For federated
authentication through LDAP or OIDC, refer to the `relevant documentation
<https://sodar-core.readthedocs.io/en/latest/app_projectroles_settings.html>`__
in SODAR Core for more details.


Creating a SODAR site in TARGET mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kiosc can be run in ``TARGET`` mode, drawing projects and users from
an upstream SODAR instance. Note that this requires an existing
SODAR instance which is running in ``SOURCE`` mode and that the
Kiosc instance is registered to it. Further description of the
``SOURCE``/``TARGET`` mode can be found in the `SODAR Core documentation
<https://sodar-core.readthedocs.io/en/latest/app_projectroles_usage.html#remote-
projects>`_.

To enable ``TARGET`` mode in your site, set ``PROJECTROLES_SITE_MODE=TARGET``
and configure the following environment variables, changing their value as
needed::

    # Allow creation of local projects
    PROJECTROLES_TARGET_CREATE=1
    # Enable synchronization with the source site
    PROJECTROLES_TARGET_SYNC_ENABLE=1
    # Time interval in minutes for synchronization
    PROJECTROLES_TARGET_SYNC_INTERVAL=5
