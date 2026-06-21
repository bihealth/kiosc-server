"""UI tests for containers views."""

import docker

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from django.urls import reverse

from containers.models import (
    Container,
    ACTION_START,
    ACTION_RESTART,
    STATE_RUNNING,
)
from containers.statemachines import connect_docker
from containers.tasks import container_task
from containers.tests.helpers import build_testdata_container, UITestBase
from containers.tests.factories import (
    ContainerFactory,
    ContainerBackgroundJobFactory,
)


class TestReverseProxyView(
    UITestBase,
):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        build_testdata_container(self.cli, 'sample-app-server')
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-server',
            tag='testing',
            container_port=80,
            host_port=14809,
        )

    def tearDown(self):
        for container in Container.objects.all():
            if container.container_id and not len(container.container_id) < 3:
                try:
                    self.cli.remove_container(
                        container.container_id, force=True, v=True
                    )
                except docker.errors.NotFound:
                    pass
        super().tearDown()

    def test_proxy_lobby(self):
        """Test GET ReverseProxyView with container not ready."""
        # We set the wrong container_port so that it will NEVER be ready
        self.container.container_port = 81
        self.container.save()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_START,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        self.container.refresh_from_db()
        self.assertEqual(self.container.state, STATE_RUNNING)
        self.login_and_redirect(
            self.superuser,
            reverse(
                'containers:detail',
                kwargs={
                    'container': str(self.container.sodar_uuid),
                },
            ),
        )
        btn = self.selenium.find_element(
            By.XPATH, '//a[@data-original-title="Open app"]'
        )
        # Selenium opens the link in a new tab
        # https://www.selenium.dev/documentation/webdriver/interactions/windows/
        original_window_handle = self.selenium.current_window_handle
        btn.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.number_of_windows_to_be(2)
        )
        new_window_handle = (
            set(self.selenium.window_handles) - {original_window_handle}
        ).pop()
        self.selenium.switch_to.window(new_window_handle)
        lobby_elem = self.selenium.find_element(By.ID, 'kiosc-lobby-text')
        self.assertIn('Check the logs for more info', lobby_elem.text)

        # Wait until the lobby phrase changes
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.staleness_of(lobby_elem)
        )
        lobby_elem = self.selenium.find_element(By.ID, 'kiosc-lobby-text')
        self.assertIn('Check the logs for more info', lobby_elem.text)

        # Now we restart start the container and make it accept connections,
        # so we should be redirected to the container page.
        self.container.container_port = 80
        self.container.save()
        bg_job = ContainerBackgroundJobFactory(
            user=self.superuser,
            action=ACTION_RESTART,
            container=self.container,
        )
        container_task(job_id=bg_job.pk)
        self.container.refresh_from_db()
        self.assertEqual(self.container.state, STATE_RUNNING)

        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.XPATH, '//h1[contains(text(), "Hello World")]')
            )
        )
