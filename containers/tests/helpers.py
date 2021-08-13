"""Helpers for the container tests."""
import uuid
import dateutil.parser

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
from containertemplates.models import (
    ContainerTemplateSite,
    ContainerTemplateProject,
)
from containertemplates.tests.factories import (
    ContainerTemplateSiteFactory,
    ContainerTemplateProjectFactory,
)


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
        self.assertEqual(ContainerTemplateSite.objects.count(), 1)

        self.containertemplateproject1 = ContainerTemplateProjectFactory()
        self.assertEqual(ContainerTemplateProject.objects.count(), 1)

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()


class TestBase(TestContainerCreationMixin, TestCase):
    """Test base class providing one project and a superuser."""

    def setUp(self):
        super().setUp()

        # Show full diff
        self.maxDiff = None

        # Setup project
        self.project = ProjectFactory()

        # Setup superuser
        self.superuser = self.make_user("superuser")
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()


def log_entry1():
    """First log entry."""
    dt = dateutil.parser.parse("2021-01-01 01:01:01.000001+00:00")
    return dt, "{} 2021/01/01 10:00:00 [info] Log entry 1".format(
        dateformat.format(dt.replace(tzinfo=None), "c") + "000Z"
    )


def log_entry1_no_date():
    """First log entry without date."""
    return "no date [info] Log entry 1"


def log_entry2():
    """Second log entry, same second but different millisecond."""
    dt = dateutil.parser.parse("2021-01-01 01:01:01.500001+00:00")
    return dt, "{} 2021/01/01 10:00:00 [info] Log entry 2".format(
        dateformat.format(dt.replace(tzinfo=None), "c") + "000Z"
    )


def log_entry3():
    """Third log entry happening the next second"""
    dt = dateutil.parser.parse("2021-01-01 01:01:02.000001+00:00")
    return dt, "{} 2021/01/01 10:00:01 [info] Log entry 3".format(
        dateformat.format(dt.replace(tzinfo=None), "c") + "000Z"
    )


class DockerMock:
    """Class to mock calls to Docker API."""

    pull = [
        {
            "progressDetail": {"total": "total", "current": "current"},
            "status": "status",
        }
    ]
    inspect_image = {"Id": "1"}
    inspect_container_started = {"State": {"Status": STATE_RUNNING}}
    inspect_container_restarted = {"State": {"Status": STATE_RUNNING}}
    inspect_container_paused = {"State": {"Status": STATE_PAUSED}}
    inspect_container_unpaused = {"State": {"Status": STATE_RUNNING}}
    inspect_container_stopped = {"State": {"Status": STATE_EXITED}}
    inspect_container_no_info = {}
    create_container = {"Id": "9", "State": {"Status": STATE_CREATED}}
    create_host_config = None
    create_networking_config = {}
    create_endpoint_config = {}
    logs = "\n".join(
        [log_entry1()[1], log_entry2()[1], log_entry3()[1]]
    ).encode("utf-8")
    logs_no_date = log_entry1_no_date().encode("utf-8")
    logs_since = "\n".join([log_entry2()[1], log_entry3()[1]]).encode("utf-8")
