"""Plugins for the containers app"""

from typing import Optional, Union
from uuid import UUID

# Projectroles dependency
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse
from projectroles.models import Project, SODAR_CONSTANTS, CAT_DELIMITER
from projectroles.plugins import (
    ProjectAppPluginPoint,
    PluginObjectLink,
    PluginCategoryStatistic,
)

from containers.models import Container
from containers.urls import urlpatterns

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)


User = get_user_model()

PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


# Samplesheets project app plugin ----------------------------------------------


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe, used in URLs)
    name = 'containers'

    #: Title (used in templates)
    title = 'Containers'

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
    icon = 'mdi:docker'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'containers:list'

    #: Description string
    description = 'Create and manage Docker containers'

    #: Required permission for accessing the app
    app_permission = 'containers.view_container'

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ['source', 'sample', 'file']

    #: Search results template
    search_template = 'containers/_search_results.html'

    #: App card template for the project details page
    details_template = 'containers/_details_card.html'

    #: App card title for the project details page
    details_title = 'Containers overview'

    #: Position in plugin ordering
    plugin_ordering = 20

    #: Display application for categories in addition to projects
    category_enable = False

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = []

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
    project_list_columns = {
        "containers": {
            "title": "Containers",
            "width": 50,
            "description": (
                "The current status of all containers "
                "defined in this project"
            ),
            "active": True,
            "ordering": 20,
            "align": "center",
        },
    }

    def get_statistics(self):
        return {
            "container_count": {
                "label": "Containers",
                "value": Container.objects.all().count(),
            },
            "containertemplates_site_count": {
                "label": "Site-wide Container Templates",
                "value": ContainerTemplateSite.objects.all().count(),
            },
            "containertemplates_project_count": {
                "label": "Project Container Templates",
                "value": ContainerTemplateProject.objects.all().count(),
            },
        }

    def get_category_stats(
        self, category: Project
    ) -> list[PluginCategoryStatistic]:
        """
        Return app statistics for the given category. Expected to return
        cumulative statistics for all projects under the category and its
        possible subcategories.

        :param category: Project object of CATEGORY type
        :return: List of PluginCategoryStatistic objects
        """
        children = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT,
            full_title__startswith=category.full_title + CAT_DELIMITER,
        )
        container_states = (
            Container.objects.filter(project__in=children)
            .values("state")
            .annotate(count=Count("state"))
        )
        stats = []
        for state_entry in container_states:
            stats.append(
                PluginCategoryStatistic(
                    plugin=self,
                    title=f'Containers {state_entry["state"].title()}',
                    value=state_entry["count"],
                    description=f'Number of {state_entry["state"]} containers in this category',
                    icon="mdi:file",
                )
            )
        return stats

    def get_project_list_value(
        self, column_id: str, project: Project, user: User
    ) -> Union[str, int, None]:
        """
        Return a value for the optional additional project list column specific
        to a project.

        :param column_id: ID of the column (string)
        :param project: Project object
        :param user: User object (current user)
        :return: String (may contain HTML), integer or None
        """
        if column_id != "containers":
            raise ValueError(f'Unexpected column_id: "{column_id}"')

        container_states = (
            Container.objects.filter(project=project)
            .values("state")
            .annotate(count=Count("state"))
        )
        if not container_states:
            return "0"

        stats = []
        for el in container_states:
            match el["state"]:
                case "running" | "restarting" | "pulling":
                    stats.append(str(el["count"]) + " running")
                case "paused" | "stopped" | "created" | "initial":
                    stats.append(str(el["count"]) + " stopped")
                case "failed" | "exited" | "dead":
                    stats.append(str(el["count"]) + " failed")
                case "deleted" | "deleting":
                    pass

        return ",</br>".join(stats)

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
        if model_str == 'Container':
            obj = self.get_object(Container, uuid)
            if obj is None:
                # This happens when we try to show timeline events
                # for deleted containers
                return None
            return PluginObjectLink(
                url=reverse(
                    'containers:detail',
                    kwargs={'container': obj.sodar_uuid},
                ),
                name=obj.get_display_name(),
                blank=True,
            )
        elif model_str == 'ContainerBackgroundJob':
            # TODO implement a view for background jobs
            pass

        return None
