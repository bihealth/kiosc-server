"""Django command for creating a toy project with an example app."""

from django.conf import settings
from django.core.management.base import BaseCommand

from containers.models import (
    Container,
)
from kiosc.users.models import User

from projectroles.constants import SODAR_CONSTANTS
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project, Role, RoleAssignment
from projectroles.plugins import PluginAPI


logger = ManagementCommandLogger(__name__)
plugin_api = PluginAPI()


class Command(BaseCommand):
    """Create a toy project with an example app."""

    #: Help message displayed on the command line.
    help = 'Create a toy project with an example app.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--category-name',
            help='Name of the top-level category for the project (if it does not exist, it will be created)',
            dest='category_name',
            type=str,
            required=False,
            default='Hello World',
        )
        parser.add_argument(
            '-p',
            '--project-name',
            help='Name of the project (if it does not exist, it will be created)',
            dest='project_name',
            type=str,
            required=False,
            default='Test Project',
        )
        parser.add_argument(
            '-a',
            '--app-name',
            help='Name of the app container (if it does not exist, it will be created)',
            dest='app_name',
            type=str,
            required=False,
            default='Example App',
        )
        parser.add_argument(
            '--private',
            help='Whether the project should be available only for the superuser',
            action='store_true',
        )

    def handle(self, *args, **options):
        """Implement the testproject command"""

        superuser = User.objects.get(
            username=settings.PROJECTROLES_DEFAULT_ADMIN
        )
        owner_role = Role.objects.get(
            name=SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
        )

        category, created = Project.objects.get_or_create(
            title=options['category_name'],
            type=SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            parent=None,
            description='A generic category for tests',
        )
        RoleAssignment.objects.get_or_create(
            user=superuser, role=owner_role, project=category
        )
        if created:
            logger.info(f'Created category {category.title}.')
        else:
            logger.info(f'Category {category.title} already existed.')

        if options['private']:
            access_role = None
        else:
            access_role = Role.objects.get(
                name=SODAR_CONSTANTS['PROJECT_ROLE_VIEWER']
            )
        project, created = Project.objects.get_or_create(
            title=options['project_name'],
            type=SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            parent=category,
            description='A project for tests',
            public_access=access_role,
        )
        RoleAssignment.objects.get_or_create(
            user=superuser, role=owner_role, project=project
        )
        if created:
            logger.info(f'Created project {project.title}.')
        else:
            logger.info(f'Project {project.title} already existed.')

        container, created = Container.objects.get_or_create(
            title='Shiny App Example',
            description='https://rocker-project.org/images/versioned/shiny.html',
            repository='rocker/shiny',
            tag='4.6',
            project=project,
            container_port=3838,
            host_port=3838,
        )
        if created:
            logger.info(f'Created container {container.title}.')
        else:
            logger.info(f'Container {container.title} already existed.')

        logger.info(
            f'All done! You can access the test app from {project.full_title}.'
        )

        # Add timeline event
        timeline = plugin_api.get_backend_api('timeline_backend')
        if timeline:
            tl_event = timeline.add_event(
                user=None,
                project=project,
                app_name='containers',
                event_name='create_toy_app',
                description='created {container}',
                status_type=timeline.TL_STATUS_OK,
            )
            tl_event.add_object(
                obj=container,
                label='container',
                name=container.get_display_name(),
            )
