# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from containerlist.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = 'containerlist'

    #: Title (used in templates)
    title = 'Container List'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:list-status'

    #: Description string
    description = 'A list of all containers'

    #: Entry point URL ID
    entry_point_url_id = 'containerlist:overview'

    #: Required permission for displaying the app
    app_permission = 'containerlist.view'
