"""Helpers for the container tests."""
import uuid

from test_plus.test import TestCase

from containers.models import Container, STATE_INITIAL
from containers.tests.factories import ProjectFactory, ContainerFactory


class TestBase(TestCase):
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

    def create_fake_uuid(self):
        """Create a fake UUID."""
        self.fake_uuid = uuid.uuid4()


class DockerMock:
    """Class to mock calls to Docker API."""

    @classmethod
    def pull(self, repository, tag, stream, decode):
        return [
            {
                "progressDetail": {"total": "total", "current": "current"},
                "status": "status",
            }
        ]

    @classmethod
    def inspect_image(self, image):
        return {"Id": "1"}

    @classmethod
    def create_container(
        self, detach, image, environment, command, ports, host_config
    ):
        return {"Id": "9"}

    @classmethod
    def create_host_config(self, port_bindings, ulimits):
        return

    @classmethod
    def start(self, container):
        return

    @classmethod
    def stop(self, container):
        return
