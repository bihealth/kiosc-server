"""
Django settings for the SODAR Django Site template.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import environ

from projectroles.constants import get_sodar_constants


SITE_PACKAGE = "kiosc"

ROOT_DIR = environ.Path(__file__) - 3
APPS_DIR = ROOT_DIR.path(SITE_PACKAGE)

# Load operating system environment variables and then prepare to use them
env = environ.Env()

# .env file, should load only in development environment
READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)

if READ_DOT_ENV_FILE:
    # Operating System Environment variables have precedence over variables
    # defined in the .env file, that is to say variables from the .env files
    # will only be used if not defined as environment variables.
    env_file = str(ROOT_DIR.path(".env"))
    env.read_env(env_file)

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

KIOSC_EMBEDDED_FILES = env.bool("KIOSC_EMBEDDED_FILES", default=True)


# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    # Default Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
]

THIRD_PARTY_APPS = [
    "crispy_forms",  # Form layouts
    "crispy_bootstrap4",
    "rules.apps.AutodiscoverRulesConfig",  # Django rules engine
    "djangoplugins",  # Django plugins
    "pagedown",  # For markdown
    "markupfield",  # For markdown
    "rest_framework",  # For API views
    "knox",  # For token auth
    "social_django",  # For OIDC authentication
    "axes",  # Django-axes for login security
    "docs",  # For the online user documentation/manual
    "dal",  # For user search combo box
    "dal_select2",
    # TODO: Add other third party apps here
    # SODAR Projectroles app
    "projectroles.apps.ProjectrolesConfig",
    # SODAR Timeline app
    "timeline.apps.TimelineConfig",
    # SODAR Background Jobs app
    "bgjobs.apps.BgjobsConfig",
    # User Profile site app
    "userprofile.apps.UserprofileConfig",
    # Admin Alerts site app
    "adminalerts.apps.AdminalertsConfig",
    # Site Info site app
    "siteinfo.apps.SiteinfoConfig",
    # API Tokens site app
    "tokens.apps.TokensConfig",
    # SODAR Cache backend app
    # NOTE: Only enable if used in your site
    # 'sodarcache.apps.SodarcacheConfig',
    # Admin Alerts site app
    "appalerts.apps.AppalertsConfig",
]

if KIOSC_EMBEDDED_FILES:
    THIRD_PARTY_APPS += [
        # SODAR Filesfolders app
        "filesfolders.apps.FilesfoldersConfig",
        "db_file_storage",  # For filesfolders
    ]

# Project apps
LOCAL_APPS = [
    # Custom users app
    "kiosc.users.apps.UsersConfig",
    "containers.apps.ContainersConfig",
    "containertemplates.apps.ContainertemplatesConfig",
    "kioscadmin.apps.KioscAdminConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # Should be the last one on the list
]

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {"sites": "kiosc.contrib.sites.migrations"}

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool("DJANGO_DEBUG", False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
FIXTURE_DIRS = (str(APPS_DIR.path("fixtures")),)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_SENDER = env("EMAIL_SENDER", default="noreply@example.com")
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX", default="")

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# TODO: add your information here
ADMINS = [("""YOUR NAME HERE""", "YOUR.EMAIL@example.com")]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
# Uses django-environ to accept uri format
# See: https://django-environ.readthedocs.io/en/latest/#supported-types
DATABASES = {"default": env.db("DATABASE_URL", default="postgres:///kiosc")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "Europe/Berlin"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR.path("templates"))],
        "OPTIONS": {
            "debug": DEBUG,
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                # Site context processors
                "projectroles.context_processors.urls_processor",
                "projectroles.context_processors.site_app_processor",
                "projectroles.context_processors.sidebar_processor",
            ],
        },
    }
]

CRISPY_TEMPLATE_PACK = "bootstrap4"

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
STATIC_ROOT = str(ROOT_DIR("staticfiles"))
STATIC_URL = "/static/"

STATICFILES_DIRS = [str(APPS_DIR.path("static"))]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
MEDIA_ROOT = str(APPS_DIR("media"))
MEDIA_URL = "/media/"

# STORAGE CONFIGURATION
# ------------------------------------------------------------------------------
# Set django-db-file-storage as the default storage (for filesfolders)
STORAGES = {
    "default": {
        "BACKEND": "db_file_storage.storage.DatabaseFileStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# PASSWORD STORAGE SETTINGS
# ------------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

# PASSWORD VALIDATION
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator"
    },
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",  # For rules
    "django.contrib.auth.backends.ModelBackend",
]  # NOTE: django-axes added after LDAP/OIDC setup

# Custom user app defaults
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "home"
LOGIN_URL = "login"

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = "slugify.slugify"

# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = "admin/"

# Celery configuration (for background jobs)
# ------------------------------------------------------------------------------
if USE_TZ:
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", "redis://localhost:6379/0")
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ["json"]
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = "json"
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = "json"
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
CELERYD_TASK_TIME_LIMIT = 5 * 60
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
CELERYD_TASK_SOFT_TIME_LIMIT = 60

# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = False
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = False


# API Settings
# ------------------------------------------------------------------------------

# SODAR API host URL
SODAR_API_DEFAULT_HOST = env.url(
    "SODAR_API_DEFAULT_HOST", "http://0.0.0.0:8000"
)
# SODAR API pagination page size
SODAR_API_PAGE_SIZE = env.int("SODAR_API_PAGE_SIZE", 100)

# SODAR API version
SODAR_API_DEFAULT_VERSION = "0.1"
SODAR_API_ALLOWED_VERSIONS = [SODAR_API_DEFAULT_VERSION]

# SODAR API media type
SODAR_API_MEDIA_TYPE = "application/your.application+json"

# Django REST framework
# ------------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "knox.auth.TokenAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": SODAR_API_PAGE_SIZE,
}


# Additional authentication settings
# ------------------------------------------------------------------------------

# Knox settings
KNOX_TOKEN_MODEL = "tokens.SODARAuthToken"

# Settings for HTTP AuthBasic
BASICAUTH_REALM = "Log in with user@DOMAIN and your password."
BASICAUTH_DISABLE = False


# LDAP configuration
# ------------------------------------------------------------------------------

# Enable LDAP if configured
ENABLE_LDAP = env.bool("ENABLE_LDAP", False)
ENABLE_LDAP_SECONDARY = env.bool("ENABLE_LDAP_SECONDARY", False)
LDAP_DEBUG = env.bool("LDAP_DEBUG", False)
# Alternative domains for detecting LDAP access by email address
LDAP_ALT_DOMAINS = env.list("LDAP_ALT_DOMAINS", None, [])

if ENABLE_LDAP:
    import ldap
    from django_auth_ldap.config import LDAPSearch

    if LDAP_DEBUG:
        ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
    # Default values
    LDAP_DEFAULT_CONN_OPTIONS = {ldap.OPT_REFERRALS: 0}
    LDAP_DEFAULT_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail",
    }

    # Primary LDAP server
    AUTH_LDAP_SERVER_URI = env.str("AUTH_LDAP_SERVER_URI", None)
    AUTH_LDAP_BIND_DN = env.str("AUTH_LDAP_BIND_DN", None)
    AUTH_LDAP_BIND_PASSWORD = env.str("AUTH_LDAP_BIND_PASSWORD", None)
    AUTH_LDAP_START_TLS = env.bool("AUTH_LDAP_START_TLS", False)
    AUTH_LDAP_CA_CERT_FILE = env.str("AUTH_LDAP_CA_CERT_FILE", None)
    AUTH_LDAP_CONNECTION_OPTIONS = {**LDAP_DEFAULT_CONN_OPTIONS}
    if AUTH_LDAP_CA_CERT_FILE:
        AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = (
            AUTH_LDAP_CA_CERT_FILE
        )
        AUTH_LDAP_CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0
    AUTH_LDAP_USER_FILTER = env.str(
        "AUTH_LDAP_USER_FILTER", "(sAMAccountName=%(user)s)"
    )
    AUTH_LDAP_USER_SEARCH_BASE = env.str("AUTH_LDAP_USER_SEARCH_BASE", None)
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        AUTH_LDAP_USER_SEARCH_BASE,
        ldap.SCOPE_SUBTREE,
        AUTH_LDAP_USER_FILTER,
    )
    AUTH_LDAP_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
    AUTH_LDAP_USERNAME_DOMAIN = env.str("AUTH_LDAP_USERNAME_DOMAIN", None)
    AUTH_LDAP_DOMAIN_PRINTABLE = env.str(
        "AUTH_LDAP_DOMAIN_PRINTABLE", AUTH_LDAP_USERNAME_DOMAIN
    )
    AUTHENTICATION_BACKENDS = [
        "projectroles.auth_backends.PrimaryLDAPBackend"
    ] + AUTHENTICATION_BACKENDS

    # Secondary LDAP server (optional)
    if ENABLE_LDAP_SECONDARY:
        AUTH_LDAP2_SERVER_URI = env.str("AUTH_LDAP2_SERVER_URI", None)
        AUTH_LDAP2_BIND_DN = env.str("AUTH_LDAP2_BIND_DN", None)
        AUTH_LDAP2_BIND_PASSWORD = env.str("AUTH_LDAP2_BIND_PASSWORD", None)
        AUTH_LDAP2_START_TLS = env.bool("AUTH_LDAP2_START_TLS", False)
        AUTH_LDAP2_CA_CERT_FILE = env.str("AUTH_LDAP2_CA_CERT_FILE", None)
        AUTH_LDAP2_CONNECTION_OPTIONS = {**LDAP_DEFAULT_CONN_OPTIONS}
        if AUTH_LDAP2_CA_CERT_FILE:
            AUTH_LDAP2_CONNECTION_OPTIONS[ldap.OPT_X_TLS_CACERTFILE] = (
                AUTH_LDAP2_CA_CERT_FILE
            )
            AUTH_LDAP2_CONNECTION_OPTIONS[ldap.OPT_X_TLS_NEWCTX] = 0
        AUTH_LDAP2_USER_FILTER = env.str(
            "AUTH_LDAP2_USER_FILTER", "(sAMAccountName=%(user)s)"
        )
        AUTH_LDAP2_USER_SEARCH_BASE = env.str(
            "AUTH_LDAP2_USER_SEARCH_BASE", None
        )
        AUTH_LDAP2_USER_SEARCH = LDAPSearch(
            AUTH_LDAP2_USER_SEARCH_BASE,
            ldap.SCOPE_SUBTREE,
            AUTH_LDAP2_USER_FILTER,
        )
        AUTH_LDAP2_USER_ATTR_MAP = LDAP_DEFAULT_ATTR_MAP
        AUTH_LDAP2_USERNAME_DOMAIN = env.str("AUTH_LDAP2_USERNAME_DOMAIN")
        AUTH_LDAP2_DOMAIN_PRINTABLE = env.str(
            "AUTH_LDAP2_DOMAIN_PRINTABLE", AUTH_LDAP2_USERNAME_DOMAIN
        )
        AUTHENTICATION_BACKENDS = [
            "projectroles.auth_backends.SecondaryLDAPBackend"
        ] + AUTHENTICATION_BACKENDS


# OpenID Connect (OIDC) configuration
# ------------------------------------------------------------------------------

ENABLE_OIDC = env.bool("ENABLE_OIDC", False)

if ENABLE_OIDC:
    AUTHENTICATION_BACKENDS = [
        "social_core.backends.open_id_connect.OpenIdConnectAuth"
    ] + AUTHENTICATION_BACKENDS
    TEMPLATES[0]["OPTIONS"]["context_processors"] += [
        "social_django.context_processors.backends",
        "social_django.context_processors.login_redirect",
    ]
    SOCIAL_AUTH_JSONFIELD_ENABLED = True
    SOCIAL_AUTH_JSONFIELD_CUSTOM = "django.db.models.JSONField"
    SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL
    SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = [
        "username",
        "name",
        "first_name",
        "last_name",
        "email",
    ]
    SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = env.str(
        "SOCIAL_AUTH_OIDC_OIDC_ENDPOINT", None
    )
    SOCIAL_AUTH_OIDC_KEY = env.str("SOCIAL_AUTH_OIDC_KEY", "CHANGEME")
    SOCIAL_AUTH_OIDC_SECRET = env.str("SOCIAL_AUTH_OIDC_SECRET", "CHANGEME")
    SOCIAL_AUTH_OIDC_USERNAME_KEY = env.str(
        "SOCIAL_AUTH_OIDC_USERNAME_KEY", "username"
    )


# Django-Axes
# ------------------------------------------------------------------------------

# NOTE: Axes backend should be the first backend in the list
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend"
] + AUTHENTICATION_BACKENDS

# Enable django-axes
AXES_ENABLED = env.bool("AXES_ENABLED", False)

if AXES_ENABLED:
    # Number of login attempts allowed before a record is created
    AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", 5)
    # Lock out user at failure if True
    AXES_LOCK_OUT_AT_FAILURE = env.bool("AXES_LOCK_OUT_AT_FAILURE", False)
    # Cooloff time for failure lock-out in hours
    AXES_COOLOFF_TIME = env.int("AXES_COOLOFF_TIME", None)
    # Lockout parameters. by default, block by username only (GRPR compliance)
    AXES_LOCKOUT_PARAMETERS = env.list(
        "AXES_LOCKOUT_PARAMETERS", default=["username"]
    )
    # Only enable lock for admin site if True
    AXES_ONLY_ADMIN_SITE = env.bool("AXES_ONLY_ADMIN_SITE", False)
    # For GDPR compliance, disable storing IP addresses
    # NOTE: We make this setting up, not a real Axes Django setting
    AXES_DISABLE_CLIENT_IP_STORAGE = env.bool(
        "AXES_DISABLE_CLIENT_IP_STORAGE", True
    )
    if AXES_DISABLE_CLIENT_IP_STORAGE:
        AXES_CLIENT_IP_CALLABLE = lambda x: None  # noqa: E731


# Logging
# ------------------------------------------------------------------------------

# Custom logging level
LOGGING_LEVEL = env.str("LOGGING_LEVEL", "DEBUG" if DEBUG else "ERROR")

# List of apps to include in logging
LOGGING_APPS = env.list(
    "LOGGING_APPS",
    default=[
        "projectroles",
        "siteinfo",
        "sodarcache",
        "timeline",
        "containers",
        "containertemplates",
    ],
)

# Path for file logging. If not set, will log only to console
LOGGING_FILE_PATH = env.str("LOGGING_FILE_PATH", None)


def set_logging(level=None):
    if not level:
        level = "DEBUG" if DEBUG else "ERROR"
    app_logger_config = {
        "level": level,
        "handlers": ["console", "file"] if LOGGING_FILE_PATH else ["console"],
        "propagate": True,
    }
    log_handlers = {
        "console": {
            "level": level,
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    }
    if LOGGING_FILE_PATH:
        log_handlers["file"] = {
            "level": level,
            "class": "logging.FileHandler",
            "filename": LOGGING_FILE_PATH,
            "formatter": "simple",
        }
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": log_handlers,
        "loggers": {a: app_logger_config for a in LOGGING_APPS},
    }


LOGGING = set_logging(DEBUG)


# General site settings
# ------------------------------------------------------------------------------

SITE_TITLE = "KIOSC"
SITE_SUBTITLE = env.str("SITE_SUBTITLE", "Beta")
SITE_INSTANCE_TITLE = env.str("SITE_INSTANCE_TITLE", "KIOSC")


# Local App Settings
# ------------------------------------------------------------------------------

REVPROXY = {
    "QUOTE_SPACES_AS_PLUS": True,
}


# Plugin settings
ENABLED_BACKEND_PLUGINS = env.list(
    "ENABLED_BACKEND_PLUGINS",
    None,
    [
        "timeline_backend",
        # TODO: add your backend plugins here
    ],
)

# Projectroles app settings

# Remote access mode: SOURCE or TARGET
PROJECTROLES_SITE_MODE = env.str("PROJECTROLES_SITE_MODE", "SOURCE")

# Enable or disable project creation if site is in TARGET mode
PROJECTROLES_TARGET_CREATE = env.bool("PROJECTROLES_TARGET_CREATE", True)

# Username of default admin for when regular users cannot be assigned to a task
PROJECTROLES_DEFAULT_ADMIN = env.str("PROJECTROLES_DEFAULT_ADMIN", "admin")

# Allow showing and synchronizing local non-admin users
PROJECTROLES_ALLOW_LOCAL_USERS = env.bool(
    "PROJECTROLES_ALLOW_LOCAL_USERS", False
)

# Allow unauthenticated users to access public projects if set true
PROJECTROLES_ALLOW_ANONYMOUS = False

# Enable project modify API
PROJECTROLES_ENABLE_MODIFY_API = False
# List of apps for executing project modify API actions in the given order. If
# not set, backend and project apps will execute in alphabetical order by name.
PROJECTROLES_MODIFY_API_APPS = []

# General projectroles settings
PROJECTROLES_DISABLE_CATEGORIES = env.bool(
    "PROJECTROLES_DISABLE_CATEGORIES", False
)
PROJECTROLES_INVITE_EXPIRY_DAYS = env.int("PROJECTROLES_INVITE_EXPIRY_DAYS", 14)
PROJECTROLES_SEND_EMAIL = env.bool("PROJECTROLES_SEND_EMAIL", False)
PROJECTROLES_EMAIL_SENDER_REPLY = env.bool(
    "PROJECTROLES_EMAIL_SENDER_REPLY", False
)
PROJECTROLES_ENABLE_SEARCH = True

# Inline HTML include to the head element of the base site template
PROJECTROLES_INLINE_HEAD_INCLUDE = env.str(
    "PROJECTROLES_INLINE_HEAD_INCLUDE", None
)


PROJECTROLES_TEMPLATE_INCLUDE_PATH = env.path(
    "PROJECTROLES_TEMPLATE_INCLUDE_PATH",
    os.path.join(APPS_DIR, "templates", "include"),
)

# Settings for syncing remote projects (interval is in minutes)
PROJECTROLES_TARGET_SYNC_ENABLE = env.bool(
    "PROJECTROLES_TARGET_SYNC_ENABLE", default=False
)
PROJECTROLES_TARGET_SYNC_INTERVAL = env.int(
    "PROJECTROLES_TARGET_SYNC_INTERVAL", default=5
)

# Optional projectroles settings
# Sidebar icon size (must be between 18-42)
PROJECTROLES_SIDEBAR_ICON_SIZE = env.int("PROJECTROLES_SIDEBAR_ICON_SIZE", 36)
# PROJECTROLES_SECRET_LENGTH = 32
# PROJECTROLES_HELP_HIGHLIGHT_DAYS = 7
# PROJECTROLES_SEARCH_PAGINATION = 5
# Role list pagination
PROJECTROLES_ROLE_PAGINATION = env.int("PROJECTROLES_ROLE_PAGINATION", 15)
# Support for viewing the site in "kiosk mode" (experimental)
# PROJECTROLES_KIOSK_MODE = env.bool("PROJECTROLES_KIOSK_MODE", False)
# Scroll project navigation with page content if set False
# PROJECTROLES_BREADCRUMB_STICKY = True
# Custom message to be displayed if site read-only mode is enabled
PROJECTROLES_READ_ONLY_MSG = env.str("PROJECTROLES_READ_ONLY_MSG", None)
# Restrict REST API user list/details access to users with project roles
PROJECTROLES_API_USER_DETAIL_RESTRICT = env.bool(
    "PROJECTROLES_API_USER_DETAIL_RESTRICT", False
)
# Support contact to be displayed for users, overrides ADMINS. Set as name:email
PROJECTROLES_SUPPORT_CONTACT = env.str("PROJECTROLES_SUPPORT_CONTACT", None)

# Hide project apps from the UI (sidebar, dropdown menus and project details)
PROJECTROLES_HIDE_PROJECT_APPS = env.list(
    "PROJECTROLES_HIDE_PROJECT_APPS", None, []
)

# Set limit for delegate roles per project (if 0, no limit is applied)
PROJECTROLES_DELEGATE_LIMIT = env.int("PROJECTROLES_DELEGATE_LIMIT", 1)

# Warn about unsupported browsers (IE)
PROJECTROLES_BROWSER_WARNING = env.bool("PROJECTROLES_BROWSER_WARNING", True)

# Disable default CDN JS/CSS includes to replace with your local files
PROJECTROLES_DISABLE_CDN_INCLUDES = env.bool(
    "PROJECTROLES_DISABLE_CDN_INCLUDES", False
)
# Inline HTML include to the head element of the base site template
PROJECTROLES_INLINE_HEAD_INCLUDE = env.str(
    "PROJECTROLES_INLINE_HEAD_INCLUDE", None
)
# Paths/URLs to optional global includes to supplement/replace default ones
PROJECTROLES_CUSTOM_JS_INCLUDES = env.list(
    "PROJECTROLES_CUSTOM_JS_INCLUDES", None, []
)
PROJECTROLES_CUSTOM_CSS_INCLUDES = env.list(
    "PROJECTROLES_CUSTOM_CSS_INCLUDES", None, []
)

# Enable profiling for debugging/analysis
PROJECTROLES_ENABLE_PROFILING = env.bool("PROJECTROLES_ENABLE_PROFILING", False)
if PROJECTROLES_ENABLE_PROFILING:
    MIDDLEWARE += ["projectroles.middleware.ProfilerMiddleware"]


# Adminalerts app settings
# Set alert email sending default in alert form
ADMINALERTS_EMAIL_SENDING_DEFAULT = env.bool(
    "ADMINALERTS_EMAIL_SENDING_DEFAULT", True
)
# Number of alerts to be shown on one page
ADMINALERTS_PAGINATION = env.int("ADMINALERTS_PAGINATION", 15)


# Appalerts app settings
APPALERTS_STATUS_INTERVAL = env.int("APPALERTS_STATUS_INTERVAL", 5)


# Bgjobs app settings
BGJOBS_PAGINATION = env.int("BGJOBS_PAGINATION", 15)


# Filesfolders app settings
FILESFOLDERS_MAX_UPLOAD_SIZE = env.int("FILESFOLDERS_MAX_UPLOAD_SIZE", 10485760)
FILESFOLDERS_MAX_ARCHIVE_SIZE = env.int(
    "FILESFOLDERS_MAX_ARCHIVE_SIZE", 52428800
)
FILESFOLDERS_SERVE_AS_ATTACHMENT = env.bool(
    "FILESFOLDERS_SERVE_AS_ATTACHMENT", False
)
FILESFOLDERS_LINK_BAD_REQUEST_MSG = env.str(
    "FILESFOLDERS_LINK_BAD_REQUEST_MSG", "Invalid request"
)
# Custom project list column example
FILESFOLDERS_SHOW_LIST_COLUMNS = env.bool(
    "FILESFOLDERS_SHOW_LIST_COLUMNS", True
)


# Timeline app settings
TIMELINE_PAGINATION = env.int("TIMELINE_PAGINATION", 15)
TIMELINE_SEARCH_LIMIT = env.int("TIMELINE_SEARCH_LIMIT", 250)


# Tokens app settings
# Restrict access to token creation for users with project roles
TOKENS_CREATE_PROJECT_USER_RESTRICT = env.bool(
    "TOKENS_CREATE_PROJECT_USER_RESTRICT", False
)

# SODAR constants (uncomment for modifying)
# SODAR_CONSTANTS = get_sodar_constants(default=True)

ICONIFY_JSON_ROOT = os.path.join(STATIC_ROOT, "iconify")


#: Maximal soft ulimit for nofiles in Docker.
KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT = env.str(
    "KIOSC_DOCKER_MAX_ULIMIT_NOFILE_SOFT", 98304
)
#: Maximal hard ulimit for nofiles in Docker.
KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD = env.str(
    "KIOSC_DOCKER_MAX_ULIMIT_NOFILE_HARD", 98304
)

#: Network mode. Can be ``host`` or ``docker-shared``.
KIOSC_NETWORK_MODE = env.str("KIOSC_NETWORK_MODE", "host")
#: Docker network name.
KIOSC_DOCKER_NETWORK = env.str("KIOSC_DOCKER_NETWORK", "kiosc-net")
#: Name of the web server Docker container.
KIOSC_DOCKER_WEB_SERVER = env.str("KIOSC_DOCKER_WEB_SERVER", "kiosc-web")
#: Min delay in seconds for container actions.
KIOSC_DOCKER_ACTION_MIN_DELAY = env.int("KIOSC_DOCKER_ACTION_MIN_DELAY", 1)
#: Max threshold for inactive running docker containers in days.
KIOSC_DOCKER_MAX_INACTIVITY = env.int("KIOSC_DOCKER_MAX_INACTIVITY", 7)
#: Max log lines allowed for a container
KIOSC_CONTAINER_MAX_LOG_LINES = env.int("KIOSC_CONTAINER_MAX_LOG_LINES", 10_000)
#: Max log lines allowed for a container
KIOSC_CONTAINER_DEFAULT_LOG_LINES = env.int(
    "KIOSC_CONTAINER_DEFAULT_LOG_LINES", 1000
)
