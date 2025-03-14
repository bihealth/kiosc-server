# Projectroles dependency
from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import ProjectAppPluginPoint

from containers.models import Container, ContainerBackgroundJob
from containers.urls import urlpatterns

PROJECT_TYPE_PROJECT = SODAR_CONSTANTS["PROJECT_TYPE_PROJECT"]


# Samplesheets project app plugin ----------------------------------------------


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = "containers"

    #: Title (used in templates)
    title = "Containers"

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: App settings definition
    # app_settings = {
    #     'allow_editing': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'BOOLEAN',
    #         'label': 'Allow Sample Sheet Editing',
    #         'description': 'Allow editing of projet sample sheets by '
    #         'authorized users',
    #         'user_modifiable': True,
    #         'default': True,
    #     },
    #     'display_config': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
    #         'type': 'JSON',
    #         'label': 'Sheet Display Configuration',
    #         'description': 'User specific JSON configuration for sample sheet'
    #         'column display',
    #     },
    #     'display_config_default': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'JSON',
    #         'label': 'Default Sheet Display Configuration',
    #         'description': 'Default JSON configuration for project sample sheet'
    #         'column display',
    #         'user_modifiable': False,
    #     },
    #     'sheet_config': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'JSON',
    #         'label': 'Sheet Editing Configuration',
    #         'description': 'JSON configuration for sample sheet editing',
    #         'user_modifiable': False,
    #     },
    #     'edit_config_min_role': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'STRING',
    #         'options': [
    #             'superuser',
    #             SODAR_CONSTANTS['PROJECT_ROLE_OWNER'],
    #             SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE'],
    #             SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
    #         ],
    #         'default': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
    #         'label': 'Minimum role for column configuration editing',
    #         'description': 'Allow per-project restriction of column '
    #         'configuration updates',
    #         'user_modifiable': True,
    #     },
    #     'sheet_sync_enable': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'BOOLEAN',
    #         'default': False,
    #         'label': 'Enable sheet synchronization',
    #         'description': 'Enable sheet synchronization from a source project',
    #         'user_modifiable': True,
    #     },
    #     'sheet_sync_url': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'STRING',
    #         'label': 'URL for sheet synchronization',
    #         'default': '',
    #         'description': 'REST API URL for sheet synchronization',
    #         'user_modifiable': True,
    #     },
    #     'sheet_sync_token': {
    #         'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
    #         'type': 'STRING',
    #         'label': 'Token for sheet synchronization',
    #         'default': '',
    #         'description': 'Access token for sheet synchronization in the source project',
    #         'user_modifiable': True,
    #     },
    # }

    #: FontAwesome icon ID string
    icon = "mdi:docker"

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = "containers:list"

    #: Description string
    description = "Create and manage Docker containers"

    #: Required permission for accessing the app
    app_permission = "containers.view_container"

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ["source", "sample", "file"]

    #: Search results template
    search_template = "containers/_search_results.html"

    #: App card template for the project details page
    details_template = "containers/_details_card.html"

    #: App card title for the project details page
    details_title = "Containers overview"

    #: Position in plugin ordering
    plugin_ordering = 20

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
        if model_str == "Container":
            obj = self.get_object(Container, uuid)
            return {
                "url": reverse(
                    "containers:detail",
                    kwargs={"container": obj.sodar_uuid},
                ),
                "label": obj.get_display_name(),
                "blank": True,
            }
        elif model_str == "ContainerBackgroundJob":
            # TODO implement a view for background jobs
            pass

        return None
