# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from kioscadmin.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = "kioscadmin"

    #: Title (used in templates)
    title = "Kiosc Admin"

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: Iconify icon
    icon = "eos-icons:admin"

    #: Description string
    description = "Admin for houskeeping Kiosc tasks"

    #: Entry point URL ID
    entry_point_url_id = "kioscadmin:overview"

    #: Required permission for displaying the app
    app_permission = "kioscadmin.admin"
