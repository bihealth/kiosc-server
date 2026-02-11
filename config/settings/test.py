"""
Test settings

- Used to run tests fast on the continuous integration server and locally
"""

from .base import *  # noqa


# DEBUG
# ------------------------------------------------------------------------------
# Turn debug off so tests run faster
DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = True

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# Note: This key only used for development and testing.
SECRET_KEY = env("DJANGO_SECRET_KEY", default="CHANGEME!!!")

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
ADMINS = [("Admin User", "admin@example.com")]
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Set False to support parallel testing, see
# https://github.com/bihealth/sodar-core/issues/1428
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025

# In-memory email backend stores messages in django.core.mail.outbox
# for unit testing purposes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_SENDER = "noreply@example.com"

# CACHING
# ------------------------------------------------------------------------------
# Speed advantages of in-memory caching without having to run Memcached
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = "django.test.runner.DiscoverRunner"
SILENCED_SYSTEM_CHECKS = ["axes.W003"]  # Silence missing axes backend warning

# PASSWORD HASHING
# ------------------------------------------------------------------------------
# Use fast password hasher so tests run faster
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATE LOADERS
# ------------------------------------------------------------------------------
# Keep templates in memory so tests run faster
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    [
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    ]
]

# Django REST framework
# ------------------------------------------------------------------------------

# Set pagination page size to 1 for easy testing
REST_FRAMEWORK["PAGE_SIZE"] = 1

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------

# NOTE: Hardcoded due to issue https://github.com/bihealth/sodar-core/issues/1767
# NOTE: Axes doesn't work with UI tests and cookie-based login, see #1810
#       in the sodar core repository (https://github.com/bihealth/sodar-core)
#       Override with AUTHENTICATION_BACKENDS_AXES when testing Axes features
AUTHENTICATION_BACKENDS = [
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# LDAP configuration
# ------------------------------------------------------------------------------

ENABLE_LDAP = False

# OpenID Connect (OIDC) configuration
# ------------------------------------------------------------------------------

ENABLE_OIDC = False

# Django-Axes
# ------------------------------------------------------------------------------

AXES_ENABLED = False  # Enable by override when testing
AXES_FAILURE_LIMIT = 3
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_TIME = None
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_ONLY_ADMIN_SITE = False
AXES_CLIENT_IP_CALLABLE = lambda x: None  # noqa: E731

# Logging
# ------------------------------------------------------------------------------

LOGGING_LEVEL = env.str("LOGGING_LEVEL", "CRITICAL")
LOGGING = set_logging(LOGGING_LEVEL)
LOGGING["loggers"]["axes"] = {
    "level": LOGGING_LEVEL,
    "handlers": ["console"],
    "propagate": False,
}  # Disable redundant axes logging in tests
LOGGING_DISABLE_CMD_OUTPUT = True

# Local App Settings
# ------------------------------------------------------------------------------


# Plugin settings
ENABLED_BACKEND_PLUGINS = ["timeline_backend", "example_backend_app"]

# Projectroles app settings
PROJECTROLES_SITE_MODE = "SOURCE"
PROJECTROLES_SEND_EMAIL = True
PROJECTROLES_SEARCH_PAGINATION = 10


# UI test settings
PROJECTROLES_TEST_UI_CHROME_OPTIONS = [
    "headless",
    "no-sandbox",  # For Gitlab-CI compatibility
    "disable-dev-shm-usage",  # For testing stability
]
PROJECTROLES_TEST_UI_WINDOW_SIZE = (1400, 1000)
PROJECTROLES_TEST_UI_WAIT_TIME = 30
PROJECTROLES_TEST_UI_LEGACY_LOGIN = env.bool(
    "PROJECTROLES_TEST_UI_LEGACY_LOGIN", False
)
PROJECTROLES_APP_SETTINGS_TEST = None

# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = True
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True
