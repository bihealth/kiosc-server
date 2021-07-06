# Projectroles dependency
from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import SiteAppPluginPoint, ProjectAppPluginPoint

from containers.urls import urlpatterns
from containertemplates.models import ContainerTemplateProject


PROJECT_TYPE_PROJECT = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]


# Samplesheets project app plugin ----------------------------------------------


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = "containertemplates"

    #: Title (used in templates)
    title = "Container Templates"

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: FontAwesome icon ID string
    icon = "octicon:repo-template-24"

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = "containertemplates:project-list"

    #: Description string
    description = "Create and manage container templates"

    #: Required permission for accessing the app
    app_permission = "containertemplates.project_view"

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ["source", "sample", "file"]

    #: Search results template
    search_template = "containertemplates/_search_results.html"

    #: App card template for the project details page
    details_template = "containertemplates/project_details_card.html"

    #: App card title for the project details page
    details_title = "Container Templates overview"

    #: Position in plugin ordering
    plugin_ordering = 10

    #: Project list columns
    project_list_columns = {
        #     'sheets': {
        #         'title': 'Sheets',
        #         'width': 70,
        #         'description': None,
        #         'active': True,
        #         'ordering': 30,
        #         'align': 'center',
        #     },
        #     'files': {
        #         'title': 'Files',
        #         'width': 70,
        #         'description': None,
        #         'active': True,
        #         'ordering': 20,
        #         'align': 'center',
        #     },
    }

    def get_object_link(self, model_str, uuid):
        """
        Return the URL for referring to a object used by the app, along with a
        label to be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: Dict or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)

        if not obj:
            return None

        elif obj.__class__ == ContainerTemplateProject:
            return {
                "url": reverse(
                    "containertemplates:project-detail",
                    kwargs={"containertemplateproject": obj.sodar_uuid},
                ),
                "label": str(obj),
                "blank": True,
            }

        return None


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
    entry_point_url_id = "containertemplates:site-list"

    #: Description string
    description = "Create and manage container templates"

    #: Required permission for accessing the app
    app_permission = "containertemplates.site_view"

    #: Enable or disable general search from project title bar
    search_enable = True

    #: App card title for the project details page
    details_title = "Container Templates overview"
