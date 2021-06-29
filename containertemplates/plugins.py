# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import SiteAppPluginPoint

from containers.urls import urlpatterns

PROJECT_TYPE_PROJECT = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]


# Samplesheets project app plugin ----------------------------------------------


class SiteAppPlugin(SiteAppPluginPoint):
    """Plugin for registering site-wide app"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = "containertemplates"

    #: Title (used in templates)
    title = "Container Templates"

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in SiteAppPluginPoint -----------------------

    #: FontAwesome icon ID string
    icon = "octicon:repo-template-24"

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = "containertemplates:list"

    #: Description string
    description = "Create and manage container templates"

    #: Required permission for accessing the app
    app_permission = "containertemplates.view"

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ["source", "sample", "file"]

    #: Search results template
    search_template = "containertemplates/_search_results.html"

    #: App card template for the project details page
    details_template = "containertemplates/_details_card.html"

    #: App card title for the project details page
    details_title = "Container Templates overview"

    #: Position in plugin ordering
    plugin_ordering = 10
