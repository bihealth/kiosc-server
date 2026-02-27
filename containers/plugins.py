"""Plugins for the containers app"""

from typing import Optional, Union
from uuid import UUID

# Projectroles dependency
from django.contrib.auth import get_user_model
from django.urls import reverse
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    ProjectAppPluginPoint,
    PluginObjectLink,
    PluginSearchResult,
)

from containers.models import (
    Container,
    ContainerBackgroundJob,
    ContainerLogEntry,
)
from containers.urls import urlpatterns


User = get_user_model()


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
    search_types = ["container", "containerbackgroundjob", "containerlogentry"]

    #: Search results template
    search_template = "containers/_search_results.html"

    #: App card template for the project details page
    details_template = "containers/_details_card.html"

    #: App card title for the project details page
    details_title = "Containers overview"

    #: Position in plugin ordering
    plugin_ordering = 20

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
        if model_str == "Container":
            obj = self.get_object(Container, uuid)
            return PluginObjectLink(
                url=reverse(
                    "containers:detail",
                    kwargs={"container": obj.sodar_uuid},
                ),
                name=obj.get_display_name(),
                blank=True,
            )
        elif model_str == "ContainerBackgroundJob":
            # TODO implement a view for background jobs
            pass

        return None

    def search(
        self,
        search_terms: list[str],
        user: User,
        search_type: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> list[PluginSearchResult]:
        """
        Return container items based on one or more search terms, user, optional
        type and optional keywords.

        :param search_terms: Search terms to be joined with the OR operator
                             (list of strings)
        :param user: User object for user initiating the search
        :param search_type: Type of objects to be searched (String)
        :param keywords: Dictionary of key/value pairs (optional)
        :return: List of PluginSearchResult objects
        """
        items = []
        if not search_type:
            containers = Container.objects.find(search_terms, keywords)
            container_bg_jobs = ContainerBackgroundJob.objects.find(
                search_terms, keywords
            )
            container_logs = ContainerLogEntry.objects.find(
                search_terms, keywords
            )
            items = (
                list(containers)
                + list(container_bg_jobs)
                + list(container_logs)
            )
            # items.sort(key=lambda x: x.title.lower())
        elif search_type == "container":
            items = Container.objects.find(search_terms, keywords)
        elif search_type == "containerbackgroundjob":
            items = ContainerBackgroundJob.objects.find(search_terms, keywords)
        elif search_type == "containerlogentry":
            items = ContainerLogEntry.objects.find(search_terms, keywords)
        if items:
            items = [
                x
                for x in items
                if isinstance(x, Container)
                and user.has_perm("containers.view_container", x)
                or user.has_perm("containers.view_container", x.container)
            ]
        ret = PluginSearchResult(
            category="all",
            title="Containers, Background Jobs, and Logs",
            search_types=[
                "container",
                "containerbackgroundjob",
                "containerlogentry",
            ],
            items=items,
        )
        return [ret]
