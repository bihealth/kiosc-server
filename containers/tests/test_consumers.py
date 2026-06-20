"""
Tests for the websocket providing real-time logs in the container detail view.
"""

from asgiref.sync import sync_to_async
import json
from threading import Thread
import time

from channels.layers import get_channel_layer
from django.conf import settings
from django.db import connection
from django.urls import re_path
from django.test import TransactionTestCase
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from projectroles.models import (
    Role,
    RoleAssignment,
    SODAR_CONSTANTS,
    ROLE_RANKING,
)
from projectroles.tests.base import (
    SeleniumSetupMixin,
    LiveUserMixin,
    UITestMixin,
)

from containers.models import (
    STATE_INITIAL,
    STATE_EXITED,
    STATE_CREATED,
    STATE_RUNNING,
    ACTION_START,
    ACTION_STOP,
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
from containers.tests.helpers import TestContainerCreationMixin
from containers.consumers import ContainerWatcherConsumer


PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
channel_layer = get_channel_layer()


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


class TestWebsocketConsumerMixin(TestContainerCreationMixin, LiveUserMixin):
    def setUp(self):
        super().setUp()

        # Setup project and users
        self.project = ProjectFactory()
        self.superuser = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.user = self.make_user('alice')
        self.user.save()
        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER, rank=ROLE_RANKING[PROJECT_ROLE_OWNER]
        )[0]
        self.role_owner_as = RoleAssignment.objects.create(
            project=self.project, user=self.superuser, role=self.role_owner
        )

        # Build the sample container image
        self.cli = connect_docker()
        build_testdata_container(self.cli, 'sample-app-logging')

        self.container1 = ContainerFactory(
            project=self.project,
            repository='sample-app-logging',
            tag='testing',
            host_port=10893,
            container_id=None,
        )
        self.container2 = ContainerFactory(
            project=self.project,
            repository='sample-app-instacrash',
            tag='testing',
            host_port=10894,
            container_id=None,
        )

        self.app = AuthMiddlewareTesting(
            URLRouter(
                [
                    re_path(
                        r'^testws/(?P<container>[0-9a-f-]+)',
                        ContainerWatcherConsumer.as_asgi(),
                    ),
                ]
            ),
            self.superuser,
        )

    def tearDown(self):
        # Give some time for the consumer to shut down
        time.sleep(3)
        super().tearDown()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container1,
        )
        container_task(job_id=bg_job.pk)
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_DELETE,
            container=self.container2,
        )
        container_task(job_id=bg_job.pk)
        # Close Django connections to the db from this thread
        connection.close()

    @classmethod
    def _run_action_job(cls, user, container, action):
        bg_job = ContainerBackgroundJobFactory(
            user=user,
            action=action,
            container=container,
        )
        container_task(job_id=bg_job.pk)
        # Close Django connections to the db from this thread
        connection.close()


class TestContainerWatcherConsumer(
    TestWebsocketConsumerMixin, TransactionTestCase
):
    async def test_websocket_consumer(self):
        """Test the websocket consumer for a previously running container"""
        # Start the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_START),
        )
        t.start()
        t.join()

        # 1. We send a websocket connection request.
        ws = WebsocketCommunicator(
            self.app, 'testws/' + str(self.container1.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertTrue(connected)

        # 2a. We send the configuration: currently just the number of log lines.
        await ws.send_to(text_data='20')

        # We receive any existing ContainerLogEntries from the db.
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'static_logs')
        self.assertIn('Pulling image', response['text'])
        self.assertIn('Pulling image succeeded', response['text'])
        self.assertIn('Starting', response['text'])
        self.assertIn('Container started successfully', response['text'])

        # We receive periodic updates from the Docker daemon.
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'container_state')
        self.assertEqual(response['state'], STATE_RUNNING)

        # This container logs an increasing sequence of numbers
        for i in range(1, 11):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'daemon_logs')
            self.assertIn(f' {i}\n', response['text'])

        await ws.disconnect()

    async def test_websocket_consumer_before_start(self):
        """Test the websocket consumer started before the container"""
        # 1. We send a websocket connection request.
        ws = WebsocketCommunicator(
            self.app, 'testws/' + str(self.container1.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertTrue(connected)

        # 2a. We send the configuration: currently just the number of log lines.
        await ws.send_to(text_data='20')

        # Since the container is not running, we expect only the container state
        # from the daemon, no logs.
        for i in range(3):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'container_state')
            self.assertEqual(response['state'], STATE_INITIAL)

        # Start the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_START),
        )
        t.start()
        t.join()

        # Now we expect pulling and task messages from the channel layer, not
        # from the db
        for i in range(6):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'channel_logs')

        # Now we try to trick the server by re-sending the text data
        await ws.send_to(text_data='20')
        # And we expect the response to come from the DB
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'static_logs')
        self.assertIn('Pulling image', response['text'])
        self.assertIn('Pulling image succeeded', response['text'])
        self.assertIn('Starting', response['text'])
        self.assertIn('Container started successfully', response['text'])

        # then we should receive either a container_state or a daemon_logs
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertIn(response['type'], ('container_state', 'daemon_logs'))

        await ws.disconnect()

    async def test_websocket_consumer_with_action(self):
        """Test the websocket consumer during a container action"""
        # Start the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_START),
        )
        t.start()
        t.join()

        # 1. We send a websocket connection request.
        ws = WebsocketCommunicator(
            self.app, 'testws/' + str(self.container1.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertTrue(connected)

        # 2a. We send the configuration: currently just the number of log lines.
        await ws.send_to(text_data='20')

        # We receive any existing ContainerLogEntries from the db.
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'static_logs')
        self.assertIn('Pulling image', response['text'])
        self.assertIn('Pulling image succeeded', response['text'])
        self.assertIn('Starting', response['text'])
        self.assertIn('Container started successfully', response['text'])

        # We receive periodic updates from the Docker daemon.
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'container_state')
        self.assertEqual(response['state'], STATE_RUNNING)

        # This container logs an increasing sequence of numbers
        for i in range(1, 11):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'daemon_logs')
            self.assertIn(f' {i}\n', response['text'])

        # Stop the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_STOP),
        )
        t.start()
        t.join()

        # We get some residual daemon logs because it takes a while to stop the container
        for i in range(60):
            response = json.loads(await ws.receive_from(timeout=10))
            if response['type'] != 'daemon_logs':
                break
        else:
            assert False, "ContainerWatcher didn't detect a change of state"

        # Now we should get just status updates
        for i in range(3):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'container_state')
            self.assertEqual(response['state'], STATE_EXITED)

        await ws.disconnect()

    async def test_websocket_consumer_instacrash(self):
        """Test the websocket consumer during a container action"""
        # Start the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container2, ACTION_START),
        )
        t.start()
        t.join()

        # 1. We send a websocket connection request.
        ws = WebsocketCommunicator(
            self.app, 'testws/' + str(self.container2.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertTrue(connected)

        # 2a. We send the configuration: currently just the number of log lines.
        await ws.send_to(text_data='20')

        # We receive any existing ContainerLogEntries from the db.
        response = json.loads(await ws.receive_from(timeout=10))
        self.assertEqual(response['type'], 'static_logs')
        self.assertIn('Pulling image', response['text'])
        self.assertIn('Pulling image succeeded', response['text'])
        self.assertIn('Starting', response['text'])
        self.assertIn('Failed to start container', response['text'])

        # We receive periodic updates from the Docker daemon.
        for i in range(3):
            response = json.loads(await ws.receive_from(timeout=10))
            self.assertEqual(response['type'], 'container_state')
            self.assertEqual(response['state'], STATE_CREATED)

        await ws.disconnect()

    async def test_websocket_consumer_permissions(self):
        # self.user (Alice) does not have a role in the project
        app = AuthMiddlewareTesting(
            URLRouter(
                [
                    re_path(
                        r'^testws/(?P<container>[0-9a-f-]+)',
                        ContainerWatcherConsumer.as_asgi(),
                    ),
                ]
            ),
            self.user,
        )
        ws = WebsocketCommunicator(
            app, 'testws/' + str(self.container1.sodar_uuid)
        )
        connected, subprotocol = await ws.connect()
        self.assertFalse(connected)


class TestContainerWatcherConsumerLive(
    SeleniumSetupMixin, UITestMixin, TestWebsocketConsumerMixin, ChannelsLiveServerTestCase
):
    def setUp(self):
        super().setUp()
        self.set_up_selenium()

    def tearDown(self):
        # Shut down Selenium
        self.selenium.execute_script("if (window.KioscContainerWatcherSocket) { window.KioscContainerWatcherSocket.close(); }")
        self.selenium.quit()
        super().tearDown()

    def test_live_stuff(self):
        """Test logs watcher in live site with selenium."""
        self.login_and_redirect(
            self.superuser, f'/containers/detail/{self.container1.sodar_uuid}'
        )
        state_elem = self.selenium.find_element(By.ID, 'id_container_state')
        logs_elem = self.selenium.find_element(By.ID, 'id_logs')
        initial_state = state_elem.text
        initial_logs = logs_elem.text
        self.assertEqual(initial_state, 'Loading...')
        self.assertEqual(initial_logs, ' Loading...')

        WebDriverWait(state_elem, 10).until(lambda el: el.text != initial_state)
        not_running_state = state_elem.text
        self.assertEqual(not_running_state, 'The container is not running yet, please start it.')

        # We start the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_START),
        )
        t.start()
        t.join()

        WebDriverWait(state_elem, 10).until(lambda el: el.text != not_running_state)
        not_accepting_state = state_elem.text
        self.assertEqual(not_accepting_state, 'The app is not accepting connections; please be patient...')

        WebDriverWait(logs_elem, 10).until(lambda el: el.text != initial_logs)
        channel_logs = logs_elem.text
        self.assertIn('Pulling image', channel_logs)
        self.assertIn('Pulling image succeeded', channel_logs)
        self.assertIn('Starting', channel_logs)
        self.assertIn('Container started successfully', channel_logs)

        # This container logs an increasing sequence of numbers: we try and
        # detect it.
        WebDriverWait(logs_elem, 10).until(lambda el: el.text != channel_logs)
        daemon_logs = logs_elem.text
        log_line_count = 1
        for log_line in daemon_logs.split('\n'):
            if '[Kiosc Task]' in log_line:
                continue
            log_date, log_text = log_line.split(' ')
            self.assertEqual(log_text, str(log_line_count))
            log_line_count += 1

        # We stop the container
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_STOP),
        )
        t.start()
        t.join()

        WebDriverWait(logs_elem, 10).until(lambda el: el.text != daemon_logs)
        stopped_logs = logs_elem.text
        self.assertIn('Stopping container succeeded', stopped_logs)

        # Finally we check the status update
        WebDriverWait(state_elem, 10).until(lambda el: el.text != not_accepting_state)
        exited_state = state_elem.text
        self.assertEqual(exited_state, 'The container is exited.')

        # But then we start the container again
        t = Thread(
            target=self._run_action_job,
            args=(self.superuser, self.container1, ACTION_START),
        )
        t.start()
        t.join()

        WebDriverWait(state_elem, 10).until(lambda el: el.text != exited_state)
        not_accepting_state = state_elem.text
        self.assertEqual(not_accepting_state, 'The app is not accepting connections; please be patient...')

        WebDriverWait(logs_elem, 10).until(lambda el: el.text != stopped_logs)
        restarted_logs = logs_elem.text
        self.assertIn('Container started successfully', restarted_logs[-1])
