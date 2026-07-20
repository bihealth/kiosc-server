"""Plugins for the containers app"""

from datetime import datetime
from typing import Optional, Union
from uuid import UUID
import logging

import docker

# Projectroles dependency
from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet
from django.urls import reverse
from projectroles.models import Project, SODAR_CONSTANTS, CAT_DELIMITER
from projectroles.plugins import (
    ProjectAppPluginPoint,
    PluginObjectLink,
    PluginCategoryStatistic,
    PluginSearchResult,
    PluginSearchResultColumn,
    PluginSearchResultCell,
    ProjectModifyPluginMixin,
)

from containers.models import (
    Container,
    ContainerLogEntry,
    STATE_CREATED,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_EXITED,
    STATE_DEAD,
    STATE_DELETING,
    STATE_DELETED,
    STATE_PULLING,
    STATE_INITIAL,
    STATE_RESTARTING,
    STATE_FAILED,
    STATE_TERMINATED,
)
from containers.urls import urlpatterns
from containers.views import ContainerModifyMixin
from containers.statemachines import connect_docker

from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)


User = get_user_model()
logger = logging.getLogger(__name__)

PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


# Samplesheets project app plugin ----------------------------------------------


class ProjectAppPlugin(
    ProjectAppPluginPoint, ProjectModifyPluginMixin, ContainerModifyMixin
):
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
    search_types = [
        'container',
        'containerlogentry',
        'containertemplate',
    ]

    #: Search results styling
    # search_css = 'containers/search.css'

    #: App card template for the project details page
    details_template = 'containers/_details_card.html'

    #: App card title for the project details page
    details_title = 'Containers Overview'

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
        'containers': {
            'title': 'Containers',
            'width': 50,
            'description': (
                'The current status of all containers defined in this project'
            ),
            'active': True,
            'ordering': 20,
            'align': 'center',
        },
    }

    @classmethod
    def _get_container_search_results(
        cls,
        items: list,
        user: User,
        **kwargs: str,
    ) -> list[PluginSearchResult]:
        rows = []
        for item in items:
            type_name = item.__class__.__name__
            match item:
                case ContainerTemplateSite():
                    project_value = project_url = None
                    container_url = reverse(
                        'containertemplates:site-detail',
                        kwargs={'containertemplatesite': item.sodar_uuid},
                    )
                case Container() | ContainerTemplateProject():
                    if not user.has_perm(
                        'containers.view_container', item.project
                    ):
                        continue
                    project_value = item.project.title
                    project_url = reverse(
                        'projectroles:detail',
                        kwargs={'project': item.project.sodar_uuid},
                    )
                    if isinstance(item, Container):
                        container_url = reverse(
                            'containers:detail',
                            kwargs={'container': item.sodar_uuid},
                        )
                    elif isinstance(item, ContainerTemplateProject):
                        container_url = reverse(
                            'containertemplates:project-detail',
                            kwargs={
                                'containertemplateproject': item.sodar_uuid
                            },
                        )
                case _:
                    logger.error(f'Unexpected search result: {item}')
                    continue
            rows.append(
                [
                    PluginSearchResultCell(
                        value=type_name,
                    ),
                    PluginSearchResultCell(
                        value=project_value,
                        value_url=project_url,
                    ),
                    PluginSearchResultCell(
                        value=f'{item.title} ({item.repository}:{item.tag})',
                        value_url=container_url,
                    ),
                    PluginSearchResultCell(
                        value=item.description,
                    ),
                ]
            )
        return rows

    @classmethod
    def _get_log_search_results(
        cls,
        search_terms: list[str],
        items: list,
        user: User,
        **kwargs: str,
    ) -> list[PluginSearchResult]:
        rows = []
        for item in items:
            if not user.has_perm(
                'containers.view_logs', item.container.project
            ):
                continue
            rows.append(
                [
                    PluginSearchResultCell(
                        value=item.date_created,
                    ),
                    PluginSearchResultCell(
                        value=item.container.project.title,
                        value_url=reverse(
                            'projectroles:detail',
                            kwargs={
                                'project': item.container.project.sodar_uuid
                            },
                        ),
                    ),
                    PluginSearchResultCell(
                        value=f'{item.container.title} ({item.container.repository}:{item.container.tag})',
                        value_url=reverse(
                            'containers:detail',
                            kwargs={'container': item.container.sodar_uuid},
                        ),
                    ),
                    PluginSearchResultCell(
                        value=item.text,
                    ),
                ]
            )
        cli = connect_docker()
        for container in Container.objects.exclude(container_id=None):
            if not user.has_perm('containers.view_logs', container.project):
                continue
            try:
                logs = cli.logs(container.container_id, timestamps=True)
            except (docker.errors.NotFound, docker.errors.NullResource) as ex:
                logger.warning('Error while searching container logs: %s', ex)
                continue
            for log in logs.decode('utf8').splitlines():
                timestamp, text = log.split(' ', maxsplit=1)
                for term in search_terms:
                    if term in text:
                        break
                else:
                    continue
                rows.append(
                    [
                        PluginSearchResultCell(
                            value=datetime.fromisoformat(timestamp),
                        ),
                        PluginSearchResultCell(
                            value=container.project.title,
                            value_url=reverse(
                                'projectroles:detail',
                                kwargs={
                                    'project': container.project.sodar_uuid
                                },
                            ),
                        ),
                        PluginSearchResultCell(
                            value=f'{container.title} ({container.repository}:{container.tag})',
                            value_url=reverse(
                                'containers:detail',
                                kwargs={'container': container.sodar_uuid},
                            ),
                        ),
                        PluginSearchResultCell(
                            value=text,
                        ),
                    ]
                )
        rows.sort(key=lambda x: (x[1].value, x[2].value, x[0].value))
        return rows

    def get_statistics(self):
        return {
            'container_count': {
                'label': 'Containers',
                'value': Container.objects.all().count(),
            },
            'containertemplates_site_count': {
                'label': 'Site-wide Container Templates',
                'value': ContainerTemplateSite.objects.all().count(),
            },
            'containertemplates_project_count': {
                'label': 'Project Container Templates',
                'value': ContainerTemplateProject.objects.all().count(),
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
            .values('state')
            .annotate(count=Count('state'))
        )
        stats = []
        for state_entry in container_states:
            stats.append(
                PluginCategoryStatistic(
                    plugin=self,
                    title=f'Containers {state_entry["state"].title()}',
                    value=state_entry['count'],
                    description=f'Number of {state_entry["state"]} containers in this category',
                    icon='mdi:file',
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
        if column_id != 'containers':
            raise ValueError(f'Unexpected column_id: "{column_id}"')

        container_states = (
            Container.objects.filter(project=project)
            .values('state')
            .annotate(count=Count('state'))
        )
        if not container_states:
            return '0'

        stats = {}
        for el in container_states:
            if el['state'] in (STATE_RUNNING, STATE_RESTARTING, STATE_PULLING):
                stats['running'] = stats.get('running', 0) + el['count']
            elif el['state'] in (
                STATE_PAUSED,
                STATE_TERMINATED,
                STATE_EXITED,
                STATE_CREATED,
                STATE_INITIAL,
            ):
                stats['stopped'] = stats.get('stopped', 0) + el['count']
            elif el['state'] in (STATE_FAILED, STATE_DEAD):
                stats['failed'] = stats.get('failed', 0) + el['count']
            elif el['state'] in (STATE_DELETED, STATE_DELETING):
                pass
            else:
                stats['unknown'] = stats.get('unknown', 0) + el['count']

        return ',</br>'.join(
            f'{count} {state}' for state, count in stats.items()
        )

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

    def perform_project_delete(self, project: Project):
        """
        Clean-up actions to be performed when a project is deleted

        Ensure that all containers belonging to the project are stopped and
        deleted.

        NOTE: the method is called only if the setting
        ``PROJECTROLES_ENABLE_MODIFY_API`` is True.

        :param project: The project being deleted
        """
        containers = Container.objects.filter(project=project)
        # NOTE: the project modify API plugin only passes the project as arg to
        # this function, not the user. Hence, we use the project owner for the
        # BackgroundJob user, as a workaround.
        user = project.get_owner().user
        for container in containers:
            self._container_delete_docker(container, user)

    def search(
        self,
        search_terms: list[str],
        user: User,
        projects: QuerySet[Project],
        **kwargs: str,
    ) -> list[PluginSearchResult]:
        """
        Return container items based on one or more search terms, user, optional
        type and optional keywords.

        NOTE: this method is also responsible for searching ContainerTemplate
        objects.

        :param search_terms: Search terms to be joined with the OR operator
                             (list of strings)
        :param user: User object for user initiating the search
        :param projects: QuerySet of projects where the terms are searched
        :param kwargs: Search options as key/value pairs (optional)
        :return: List of PluginSearchResult objects
        """
        container_items = []
        if kwargs.get('type', 'container') == 'container':
            container_items.extend(
                Container.objects.find(search_terms, projects, kwargs)
            )
        if kwargs.get('type', 'containertemplate') == 'containertemplate':
            container_items.extend(
                ContainerTemplateProject.objects.find(
                    search_terms, projects, kwargs
                )
            )
            container_items.extend(
                ContainerTemplateSite.objects.find(
                    search_terms, projects, kwargs
                )
            )
        log_items = []
        if kwargs.get('type', 'containerlogentry') == 'containerlogentry':
            log_items.extend(
                ContainerLogEntry.objects.find(search_terms, projects, kwargs)
            )
        ret = [
            PluginSearchResult(
                category='containers',
                title='Containers and Container Templates',
                search_types=[
                    'container',
                    'containertemplate',
                ],
                columns=[
                    PluginSearchResultColumn(
                        title='Type',
                        column_class='text-nowrap',
                    ),
                    PluginSearchResultColumn(
                        title='Project',
                        overflow=True,
                    ),
                    PluginSearchResultColumn(
                        title='Container',
                        overflow=True,
                        highlight=True,
                    ),
                    PluginSearchResultColumn(
                        title='Description',
                        overflow=True,
                        highlight=True,
                    ),
                ],
                rows=self._get_container_search_results(
                    container_items, user, **kwargs
                ),
                table_class='kiosc-container-search-table',
            ),
            PluginSearchResult(
                category='logs',
                title='Containers Logs',
                search_types=[
                    'containerlogentry',
                ],
                columns=[
                    PluginSearchResultColumn(
                        title='Datetime',
                        column_class='text-nowrap',
                    ),
                    PluginSearchResultColumn(
                        title='Project',
                        overflow=True,
                    ),
                    PluginSearchResultColumn(
                        title='Container',
                        overflow=True,
                        highlight=True,
                    ),
                    PluginSearchResultColumn(
                        title='Text',
                        overflow=True,
                        highlight=True,
                    ),
                ],
                rows=self._get_log_search_results(
                    search_terms, log_items, user, **kwargs
                ),
                table_class='kiosc-log-search-table',
            ),
        ]
        return ret
