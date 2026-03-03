import io
from unittest.mock import patch

from django.core.management import call_command

from containers.models import STATE_RUNNING, STATE_EXITED, Container
from containers.tests.helpers import TestBase, DockerMock


class TestCommandMixin:
    def run_command(self, *args):
        out = io.StringIO()
        call_command(self.command, *args, stdout=out)
        return out.getvalue()


class TestStopAll(TestCommandMixin, TestBase):
    """Tests for management command ``stop_all``."""

    command = "stop_all"

    def test_no_containers(self):
        out = self.run_command()
        self.assertIn("Command successfully finished", out)

    @patch("containers.tasks.container_task.apply_async")
    @patch("docker.api.client.APIClient.inspect_container")
    def test_one_container(self, inspect_container, apply_async):
        self.create_one_container()
        self.container1.state = STATE_RUNNING
        self.container1.save()

        out = self.run_command()

        self.assertIn("{} stopped".format(self.container1.title), out)
        self.assertIn("Command successfully finished", out)

        inspect_container.assert_called()
        apply_async.assert_called()


class TestRemoveStopped(TestCommandMixin, TestBase):
    """Tests for management command ``remove_stopped``."""

    command = "remove_stopped"

    def test_no_containers(self):
        out = self.run_command()
        self.assertIn("Command successfully finished", out)

    @patch("docker.api.client.APIClient.inspect_container")
    def test_stopped_and_running_container_dry_run(self, inspect_container):
        self.create_two_containers()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.container2.state = STATE_EXITED
        self.container2.save()

        inspect_container.side_effect = [DockerMock.inspect_container_stopped]

        out = self.run_command()

        self.assertIn("{} would be removed".format(self.container2.title), out)
        self.assertIn("Command successfully finished (dry-run)", out)

    @patch("containers.tasks.container_task.run")
    @patch("docker.api.client.APIClient.inspect_container")
    def test_stopped_and_running_container(
        self, inspect_container, container_task
    ):
        self.create_two_containers()
        self.container1.state = STATE_RUNNING
        self.container1.save()
        self.container2.state = STATE_EXITED
        self.container2.save()

        inspect_container.side_effect = [DockerMock.inspect_container_stopped]

        out = self.run_command("--remove")

        container_task.assert_called()

        self.assertIn("{} removed".format(self.container2.title), out)
        self.assertIn("Command successfully finished", out)

        self.assertEqual(Container.objects.count(), 1)


class TestStopUnused(TestCommandMixin, TestBase):
    """Tests for management command ``stop_unused``.

    Thoroughly tested in ``kioscadmin/test_tasks.py``
    """

    command = "stop_unused"

    @patch("kioscadmin.tasks.stop_inactive_containers.run")
    def test_no_containers(self, stop_inactive_containers):
        out = self.run_command()
        stop_inactive_containers.assert_called()
        self.assertIn("Command successfully finished", out)
