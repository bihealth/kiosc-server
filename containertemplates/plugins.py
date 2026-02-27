"""Plugins for the containertemplates app"""

from typing import Optional, Union
from uuid import UUID

# Projectroles dependency
from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    SiteAppPluginPoint,
    ProjectAppPluginPoint,
    PluginObjectLink,
)

from containertemplates.urls import urlpatterns
from containertemplates.models import (
    ContainerTemplateProject,
    ContainerTemplateSite,
)


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

    #: App setting definitions
    #:
    #: Example ::
    #:
    #:     app_settings = [
    #:         PluginAppSettingDef(
    #:             name='example_setting',  # Must be unique within plugin
    #:             scope=APP_SETTING_SCOPE_PROJECT,
    #:             type=APP_SETTING_TYPE_STRING,
    #:             default='example',  # Optional
    #:             label='Example setting',  # Optional
    #:             placeholder='Enter example setting here',  # Optional
    #:             description='Example user setting',  # Optional
    #:             options=['example', 'example2'],  # Optional, only for STRING
    #:                                               # or INTEGER settings
    #:             user_modifiable=True,  # Optional, show/hide in forms
    #:             global_edit=False,  # Optional, enable/disable editing on
    #:                                 # target sites
    #:             widget_attrs={},  # Optional, widget attrs for forms
    #:         )
    #:    ]
    app_settings = []

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

    #: Optional custom project list column definition
    #:
    #: Example ::
    #:
    #:     project_list_columns = {
    #:         'column_id': {
    #:             'title': 'Column Title',
    #:             'width': 100,  # Desired width of column in pixels
    #:             'description': 'Description',  # Optional description string
    #:             'active': True,  # Boolean for whether the column is active
    #:             'ordering': 50,  # Integer for ordering the columns
    #:             'align': 'left'  # Alignment of content
    #:         }
    #:     }
    project_list_columns = {}

    #: Display application for categories in addition to projects
    category_enable = False

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = []

    def get_object_link(
        self, model_str: str, uuid: Union[str, UUID]
    ) -> Optional[PluginObjectLink]:
        """
        Return the URL for referring to a object used by the app, along with a
        label to be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        if model_str == "ContainerTemplateProject":
            obj = self.get_object(ContainerTemplateProject, uuid)
            return PluginObjectLink(
                url=reverse(
                    "containertemplates:project-detail",
                    kwargs={"containertemplateproject": obj.sodar_uuid},
                ),
                name=str(obj),
                blank=True,
            )

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

    #: Description string
    description = "Create and manage container templates"

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = "containertemplates:site-list"

    #: Required permission for accessing the app
    app_permission = "containertemplates.site_view"

    #: User settings definition
    #:
    #: Example ::
    #:
    #:     app_settings = [
    #:         PluginAppSettingDef(
    #:             name='example_setting',  # Must be unique within plugin
    #:             scope=APP_SETTING_SCOPE_USER,  # Use USER or SITE
    #:             type=APP_SETTING_TYPE_STRING,
    #:             default='example',  # Optional
    #:             label='Example setting',  # Optional
    #:             placeholder='Enter example setting here',  # Optional
    #:             description='Example user setting',  # Optional
    #:             options=['example', 'example2'],  # Optional, only for STRING
    #:                                               # or INTEGER settings
    #:             user_modifiable=True,  # Optional, show/hide in forms
    #:             global_edit=False,  # Optional, enable/disable editing on
    #:                                 # target sites
    #:             widget_attrs={},  # Optional, widget attrs for forms
    #:         )
    #:    ]
    app_settings = []

    #: Enable or disable general search from project title bar
    search_enable = True

    #: App card title for the project details page
    details_title = "Container Templates overview"

    #: List of names for plugin specific Django settings to display in siteinfo
    info_settings = []

    def get_object_link(
        self, model_str: str, uuid: Union[str, UUID]
    ) -> Optional[PluginObjectLink]:
        """
        Return the URL for referring to a object used by the app, along with a
        label to be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        if model_str == "ContainerTemplateSite":
            obj = self.get_object(ContainerTemplateSite, uuid)
            return PluginObjectLink(
                url=reverse(
                    "containertemplates:site-detail",
                    kwargs={"containertemplatesite": obj.sodar_uuid},
                ),
                name=str(obj),
                blank=True,
            )

        return None
