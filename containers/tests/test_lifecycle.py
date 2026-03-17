"""Test state machines."""

from pathlib import Path

from django.test import override_settings

from containers.models import (
    ContainerLogEntry,
    ACTION_START,
    ACTION_STOP,
    ACTION_RESTART,
    ACTION_PAUSE,
    ACTION_UNPAUSE,
    ACTION_DELETE,
    STATE_CREATED,
    STATE_EXITED,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_FAILED,
    STATE_DELETED,
)
from containers.statemachines import connect_docker
from containers.tasks import container_task, sync_container_state
from containers.tests.factories import (
    ContainerFactory,
    ContainerBackgroundJobFactory,
)
from containers.tests.helpers import TestBase


def build_testdata_container(cli, dockerfile_name):
    dockerfile_path = (
        Path(__file__).parent / "testdata" / (dockerfile_name + ".Dockerfile")
    )
    with open(dockerfile_path, "rb") as f:
        stream = cli.build(fileobj=f, tag=dockerfile_name + ":testing")
    # Block until building is done
    _ = list(stream)


@override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
class TestContainerLifecycle(TestBase):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        # Build the sample container image
        build_testdata_container(self.cli, "sample-app-logging")

        self.container = ContainerFactory(
            project=self.project,
            repository="sample-app-logging",
            tag="testing",
            host_port=0,
            container_id=None,
        )

    def _test_container_start(self):
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn("Starting succeeded", logs)
        self.assertEqual(self.container.state, STATE_RUNNING)
        self.assertTrue(self.container.image_id.startswith("sha256:"))
        # Test from the daemon
        for container in self.cli.containers():
            if container["Id"] == self.container.container_id:
                self.assertEqual(container["State"], STATE_RUNNING)
                break
        else:
            raise RuntimeError("Container is not running")

    def _test_container_pause(self):
        self.assertEqual(self.container.state, STATE_RUNNING)
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_PAUSE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn("Pausing succeeded", logs)
        self.assertEqual(self.container.state, STATE_PAUSED)
        # Test from the daemon
        for container in self.cli.containers():
            if container["Id"] == self.container.container_id:
                self.assertEqual(container["State"], STATE_PAUSED)
                break
        else:
            raise RuntimeError("Container is not paused")

    def _test_container_unpause(self):
        self.assertEqual(self.container.state, STATE_PAUSED)
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_UNPAUSE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn("Unpausing succeeded", logs)
        self.assertEqual(self.container.state, STATE_RUNNING)
        # Test from the daemon
        for container in self.cli.containers():
            if container["Id"] == self.container.container_id:
                self.assertEqual(container["State"], STATE_RUNNING)
                break
        else:
            raise RuntimeError("Container is not unpaused")

    def _test_container_stop(self):
        self.assertEqual(self.container.state, STATE_RUNNING)
        image_id = self.container.image_id
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_STOP,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn("Stopping succeeded", logs)
        self.assertEqual(self.container.state, STATE_EXITED)
        # Test from the daemon (container should not be found)
        for container in self.cli.containers():
            if container["ImageID"] == image_id:
                raise RuntimeError("Container did not stop successfully")

    def _test_container_restart(self):
        self.assertEqual(self.container.state, STATE_EXITED)
        container_id_before = self.container.container_id
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_RESTART,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        self.assertIn("Deleting succeeded", logs)
        container_id_after = self.container.container_id
        self.assertNotEqual(container_id_before, container_id_after)
        self.assertEqual(self.container.state, STATE_RUNNING)
        # Test from the daemon
        for container in self.cli.containers():
            if container["Id"] == self.container.container_id:
                self.assertEqual(container["State"], STATE_RUNNING)
                break
        else:
            raise RuntimeError("Container did not restart")

    def _test_container_delete(self, initial=STATE_RUNNING):
        self.assertEqual(self.container.state, initial)
        image_id = self.container.image_id
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        self.assertEqual(self.container.state, STATE_DELETED)
        # Test from the daemon (container should not be found)
        for container in self.cli.containers(all=True):
            if container["ImageID"] == image_id:
                raise RuntimeError("Container was not deleted successfully")

    def test_container_lifecycle(self):
        """Test a typical container lifecycle"""
        self._test_container_start()
        self._test_container_pause()
        self._test_container_unpause()
        self._test_container_stop()
        self._test_container_restart()
        self._test_container_delete()

    def test_container_crash_stop(self):
        """Simulate a container crash"""
        self._test_container_start()
        self.cli.stop(self.container.container_id)
        self.assertEqual(self.container.state, STATE_RUNNING)
        old_container_id = self.container.container_id
        sync_container_state(self.container)
        self.container.refresh_from_db()
        self.assertEqual(self.container.state, STATE_EXITED)
        self.assertEqual(old_container_id, self.container.container_id)
        self._test_container_delete(initial=STATE_EXITED)

    def test_container_crash_delete(self):
        """Simulate a container deletion"""
        self._test_container_start()
        self.cli.remove_container(self.container.container_id, force=True)
        self.assertEqual(self.container.state, STATE_RUNNING)
        sync_container_state(self.container)
        self.container.refresh_from_db()
        self.assertEqual(self.container.state, STATE_FAILED)
        self.assertEqual(self.container.container_id, "")
        # No need to delete the container again

    def test_container_delete_unsynced(self):
        """Test situation where an unsynced container gets deleted"""
        # NOTE: This test failed before #200
        self._test_container_start()
        self.container.state = STATE_EXITED  # But it's actually still running
        self.container.save()
        self._test_container_delete(initial=STATE_EXITED)


@override_settings(KIOSC_DOCKER_ACTION_MIN_DELAY=0)
class TestContainerCrash(TestBase):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        # Build the sample container image
        build_testdata_container(self.cli, "sample-app-instacrash")

        self.container = ContainerFactory(
            project=self.project,
            repository="sample-app-instacrash",
            tag="testing",
            host_port=0,
            container_id=None,
        )

    def test_start_and_crash(self):
        """Test starting a container that crashes"""
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        # Test from the database
        self.container.refresh_from_db()
        logs = [log.text for log in ContainerLogEntry.objects.all()]
        sync_container_state(self.container)
        self.assertNotIn("Starting succeeded", logs)
        self.assertIn("Action failed: start", logs)
        self.assertEqual(self.container.state, STATE_FAILED)
        # self.assertTrue(self.container.image_id.startswith("sha256:"))
        self.assertIsNone(self.container.container_id)
        # Test from the daemon
        for container in self.cli.containers(all=True):
            if container["Image"] == 'sample-app-instacrash:testing':
                self.assertEqual(container["State"], STATE_CREATED)
                break
        else:
            raise RuntimeError("Container was not found")
