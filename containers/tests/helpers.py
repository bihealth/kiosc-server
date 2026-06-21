"""Helpers for the container tests."""

import dateutil.parser
from pathlib import Path
import uuid

from django.conf import settings
from django.utils import dateformat
from test_plus.test import TestCase

from containers.models import (
    Container,
    STATE_INITIAL,
    STATE_CREATED,
    STATE_RUNNING,
    STATE_EXITED,
    STATE_PAUSED,
)
from containers.tests.factories import ProjectFactory, ContainerFactory
from containers.views_api import (
    CONTAINERS_API_MEDIA_TYPE,
    CONTAINERS_API_DEFAULT_VERSION,
)
from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)
from containertemplates.tests.factories import (
    ContainerTemplateSiteFactory,
    ContainerTemplateProjectFactory,
)
from projectroles.models import (
    Role,
    RoleAssignment,
    SODAR_CONSTANTS,
    ROLE_RANKING,
)
from projectroles.tests.base import APIViewTestBase
from projectroles.plugins import PluginAPI
from timeline.models import TL_STATUS_OK


PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
APP_NAME = 'containers'

plugin_api = PluginAPI()
timeline = plugin_api.get_backend_api('timeline_backend')


def build_testdata_container(cli, dockerfile_name):
    dockerfile_path = (
        Path(__file__).parent / 'testdata' / (dockerfile_name + '.Dockerfile')
    )
    with open(dockerfile_path, 'rb') as f:
        stream = cli.build(fileobj=f, tag=dockerfile_name + ':testing')
    # Block until building is done
    _ = list(stream)


class TestContainerCreationMixin:
    def create_one_container(self):
        """Create one container assigned to the project."""
        self.container1 = ContainerFactory(project=self.project)
        self.assertEqual(Container.objects.count(), 1)
        self.assertEqual(self.container1.state, STATE_INITIAL)

    def create_two_containers(self):
        """Create two containers in the same project."""
        self.create_one_container()
        self.container2 = ContainerFactory(project=self.project)
        self.assertEqual(Container.objects.count(), 2)
        self.assertEqual(self.container2.state, STATE_INITIAL)

    def create_containertemplates(self):
        """Create one containertemplatesite."""
        self.containertemplatesite1 = ContainerTemplateSiteFactory()
        # NOTE: One ContainerTemplateSite object already exists because it's
        # created with a data migration (0009_create_default_template) in
        # containertemplates
        self.assertEqual(ContainerTemplateSite.objects.count(), 2)

        self.containertemplateproject1 = ContainerTemplateProjectFactory()
        self.assertEqual(ContainerTemplateProject.objects.count(), 1)

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()

    def create_container_event(
        self,
        container,
        user=None,
        event_name='test_event',
        status_type=TL_STATUS_OK,
        status_description='status description',
    ):
        """Create a container event"""
        tl_event = timeline.add_event(
            project=container.project,
            app_name=APP_NAME,
            user=user,
            event_name=event_name,
            description='event description for {container}',
        )
        tl_event.add_object(
            obj=container,
            label='container',
            name=container.get_display_name(),
        )
        tl_event.set_status(status_type, status_description)
        return tl_event


class TestBase(TestContainerCreationMixin, TestCase):
    """Test base class providing one project and a superuser."""

    def setUp(self):
        super().setUp()

        # Show full diff
        self.maxDiff = None

        # Setup project
        self.project = ProjectFactory()

        # Setup superuser
        self.superuser = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

        # Setup regular owner user
        self.user = self.make_user('alice')
        self.user.save()

        # Setup regular user with no roles
        self.user_no_roles = self.make_user('bob')
        self.user_no_roles.save()

        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER, rank=ROLE_RANKING[PROJECT_ROLE_OWNER]
        )[0]
        self.role_owner_as = RoleAssignment.objects.create(
            project=self.project, user=self.user, role=self.role_owner
        )


class ContainersAPIViewTestBase(APIViewTestBase):
    """Base class for containers API tests"""

    media_type = CONTAINERS_API_MEDIA_TYPE
    api_version = CONTAINERS_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()


def log_entry1():
    """First log entry."""
    dt = dateutil.parser.parse('2021-01-01 01:01:01.000001+00:00')
    return (
        dt,
        '{} 2021/01/01 10:00:00 [info] Log entry 1'.format(
            dateformat.format(dt.replace(tzinfo=None), 'c') + '000Z'
        ),
    )


def log_entry1_no_date():
    """First log entry without date."""
    return 'no date [info] Log entry 1'


def log_entry2():
    """Second log entry, same second but different millisecond."""
    dt = dateutil.parser.parse('2021-01-01 01:01:01.500001+00:00')
    return (
        dt,
        '{} 2021/01/01 10:00:00 [info] Log entry 2'.format(
            dateformat.format(dt.replace(tzinfo=None), 'c') + '000Z'
        ),
    )


def log_entry3():
    """Third log entry happening the next second"""
    dt = dateutil.parser.parse('2021-01-01 01:01:02.000001+00:00')
    return (
        dt,
        '{} 2021/01/01 10:00:01 [info] Log entry 3'.format(
            dateformat.format(dt.replace(tzinfo=None), 'c') + '000Z'
        ),
    )


class DockerMock:
    """Class to mock calls to Docker API."""

    pull = [
        {
            'progressDetail': {'total': 'total', 'current': 'current'},
            'status': 'status',
        }
    ]
    inspect_image = {'Id': '1', 'RepoTags': ['repository0:latest']}
    inspect_container_started = {'State': {'Status': STATE_RUNNING}}
    inspect_container_restarted = {'State': {'Status': STATE_RUNNING}}
    inspect_container_paused = {'State': {'Status': STATE_PAUSED}}
    inspect_container_unpaused = {'State': {'Status': STATE_RUNNING}}
    inspect_container_stopped = {'State': {'Status': STATE_EXITED}}
    inspect_container_no_info = {}
    create_container = {'Id': '9', 'State': {'Status': STATE_CREATED}}
    create_host_config = None
    create_networking_config = {}
    create_endpoint_config = {}
    logs = '\n'.join(
        [log_entry1()[1], log_entry2()[1], log_entry3()[1]]
    ).encode('utf-8')
    logs_no_date = log_entry1_no_date().encode('utf-8')
    logs_since = '\n'.join([log_entry2()[1], log_entry3()[1]]).encode('utf-8')

    networks = [{'Id': 'abcdef'}]
    inspect_network = {
        'Name': 'network1',
        'Id': 'abcdef',
        'Driver': 'host',
        'IPAM': {
            'Config': [{'Subnet': '172.17.0.0/16', 'Gateway': '172.17.0.1'}]
        },
        'Containers': {
            '9': {'Name': 'container1', 'IPv4Address': '172.17.0.5/16'},
        },
    }
    images = [
        {
            'Id': 'sha256:abcdef',
            'RepoTags': ['docker.io/category/project:1.0.0'],
        }
    ]
    volumes = {
        'Volumes': [
            {'Mountpoint': '/var/lib/docker/volumes/volume1', 'Name': 'abcdef'}
        ]
    }
    containers = [
        {'Id': 'abcedf', 'Names': ['/container1'], 'Image': 'sha256:abcdef'}
    ]
