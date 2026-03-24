"""
Tests for the websocket providing real-time logs in the container detail view.
"""

from asgiref.sync import sync_to_async

from django.conf import settings
from django.urls import re_path
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from projectroles.tests.base import (
    SeleniumSetupMixin,
    LiveUserMixin,
    UITestMixin,
)

from containers.models import (
    ACTION_START,
    ACTION_DELETE,
)
from containers.statemachines import connect_docker
from containers.tasks import container_task
from containers.tests.factories import (
    ProjectFactory,
    ContainerFactory,
    ContainerBackgroundJobFactory,
)
from containers.tests.test_lifecycle import build_testdata_container
from containers.tests.helpers import TestBase
from containers.consumers import LogWatcherConsumer


class AuthMiddlewareTesting:
    """
    Custom middleware that can authenticate as any user.
    To be used only for testing!
    """

    def __init__(self, app, user):
        self.app = app
        self.user = user

    async def __call__(self, scope, receive, send):
        scope['user'] = self.user
        return await self.app(scope, receive, send)


class TestLogWatcherConsumer(TestBase):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        # Build the sample container image
        build_testdata_container(self.cli, 'sample-app-logging')

        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-logging',
            tag='testing',
            host_port=0,
            container_id=None,
        )
        # Start the container
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)

    def tearDown(self):
        super().tearDown()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)

    async def test_websocket_consumer(self):
        # Connect the websocket
        app = AuthMiddlewareTesting(
            URLRouter(
                [
                    re_path(
                        r'^testws/(?P<container>[0-9a-f-]+)',
                        LogWatcherConsumer.as_asgi(),
                    ),
                ]
            ),
            self.superuser,
        )
        ws = WebsocketCommunicator(
            app, 'testws/' + str(self.container.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertTrue(connected)
        await ws.send_to(text_data='20')
        # This container logs the numbers from 1 to 100.
        # Here we check the first 20 lines of logs.
        for expected in range(1, 21):
            response = await ws.receive_from(timeout=10)
            timestamp, number = response.split()
            self.assertEqual(number, str(expected))
        await ws.disconnect()


class TestLogWatcherConsumerLive(
    SeleniumSetupMixin, LiveUserMixin, UITestMixin, ChannelsLiveServerTestCase
):
    def setUp(self):
        super().setUp()

        self.set_up_selenium()

        # Setup project
        self.project = ProjectFactory()

        # Setup superuser
        self.superuser = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

        # Setup and start container
        self.cli = connect_docker()
        build_testdata_container(self.cli, 'sample-app-logging')
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-logging',
            tag='testing',
            host_port=0,
            container_id=None,
        )
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)

    def tearDown(self):
        super().tearDown()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        self.selenium.quit()

    async def test_live_stuff(self):
        """Test logs watcher in live site with selenium."""
        await sync_to_async(self.login_and_redirect)(
            self.superuser, f'/containers/detail/{self.container.sodar_uuid}'
        )
        elem = self.selenium.find_element(By.ID, 'id_logs')
        initial_text = elem.text
        self.assertEqual(initial_text, 'Waiting for logs...')
        WebDriverWait(elem, 10).until(lambda el: el.text != initial_text)
        final_text = elem.text
        # This container logs the numbers from 1 to 100.
        # Here we check the first few lines of logs (how many depends on
        # when selenium did the polling).
        for expected, line in enumerate(final_text.splitlines(), 1):
            timestamp, number = line.split()
            self.assertEqual(number, str(expected))


class TestLogWatcherConsumerCrashing(TestBase):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        # Build the sample container image
        build_testdata_container(self.cli, 'sample-app-instacrash')

        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-instacrash',
            tag='testing',
            host_port=0,
            container_id=None,
        )
        # Start the container
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)

    def tearDown(self):
        super().tearDown()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)

    async def test_websocket_consumer(self):
        # Connect the websocket
        app = AuthMiddlewareTesting(
            URLRouter(
                [
                    re_path(
                        r'^testws/(?P<container>[0-9a-f-]+)',
                        LogWatcherConsumer.as_asgi(),
                    ),
                ]
            ),
            self.superuser,
        )
        ws = WebsocketCommunicator(
            app, 'testws/' + str(self.container.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertFalse(connected)
