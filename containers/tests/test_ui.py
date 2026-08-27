"""UI tests for containers views."""

import docker

from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


from containers.models import (
    Container,
    ContainerRemoteMount,
    ACTION_START,
    ACTION_RESTART,
    STATE_RUNNING,
)
from containers.tasks import container_task
from containers.tests.helpers import build_testdata_container, UITestBase
from containers.tests.factories import (
    ContainerFactory,
    ContainerBackgroundJobFactory,
)


class TestContainerCreateView(UITestBase):
    def test_container_form_markdown(self):
        """Test the markdown input field in ContainerCreateView form UI"""
        self.login_and_redirect(
            self.superuser,
            reverse(
                'containers:create',
                kwargs={
                    'project': str(self.project.sodar_uuid),
                },
            ),
        )
        bold_btn = self.selenium.find_element(
            By.CSS_SELECTOR, '#div_id_description .markdown-bold'
        )
        bold_btn.click()
        input = self.selenium.find_element(
            By.CSS_SELECTOR, '#div_id_description .ace_text-input'
        )
        input.send_keys('hello world')
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#div_id_description .ace_content'),
                '**hello world**',
            )
        )
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element_attribute(
                (By.CSS_SELECTOR, '#div_id_description .martor-preview'),
                'innerHTML',
                '<p><strong>hello world</strong> </p>',
            )
        )

    def test_remote_mounts_form(self):
        """Test the remote mounts inline form"""
        self.login_and_redirect(
            self.superuser,
            reverse(
                'containers:create',
                kwargs={
                    'project': str(self.project.sodar_uuid),
                },
            ),
        )
        formsets = self.selenium.find_elements(
            By.CLASS_NAME, 'kiosc-remote-mount-form'
        )
        # No formset is visible initially
        for formset in formsets:
            self.assertFalse(formset.is_displayed())
        add_mount_btn = self.selenium.find_element(
            By.ID, 'kiosc-add-remote-mount-btn'
        )
        # The first two formsets become visible
        add_mount_btn.click()
        add_mount_btn.click()
        self.assertTrue(formsets[0].is_displayed())
        self.assertTrue(formsets[1].is_displayed())
        for i in range(2, len(formsets)):
            self.assertFalse(formsets[i].is_displayed())
        # We write something in the "Destination" field of the first formset
        formsets[0].find_element(By.ID, 'id_remote_mounts-0-dest').send_keys(
            '/kiosc'
        )
        # We dismiss the first formset
        self.selenium.find_element(
            By.CLASS_NAME, 'kiosc-dismiss-remote-mount-btn'
        ).click()
        # Now only the second formset is visible
        self.assertFalse(formsets[0].is_displayed())
        self.assertTrue(formsets[1].is_displayed())
        for i in range(2, len(formsets)):
            self.assertFalse(formsets[i].is_displayed())
        # We add the first formset back and check that it is clean
        # (the "Destination" field should be empty)
        add_mount_btn.click()
        self.assertEqual(
            formsets[0].find_element(By.ID, 'id_remote_mounts-0-dest').text, ''
        )


class TestContainerDetailView(UITestBase):
    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(
            project=self.project,
            description='**hello**',
            repository='sample-app-server',
            tag='testing',
            container_port=80,
            host_port=14809,
        )

    def test_container_detail_markdown(self):
        """Test the markdown field in ContainerDetailView UI"""
        self.login_and_redirect(
            self.superuser,
            reverse(
                'containers:detail',
                kwargs={
                    'container': str(self.container.sodar_uuid),
                },
            ),
        )
        content = self.selenium.find_element(
            By.CSS_SELECTOR, '#kiosc-container-detail-description'
        )
        self.assertIn(
            '<p><strong>hello</strong></p>', content.get_attribute('innerHTML')
        )


class TestContainerUpdateView(UITestBase):
    def setUp(self):
        super().setUp()
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-volume',
            tag='testing',
            container_port=80,
            host_port=11889,
        )
        ContainerRemoteMount.objects.create(
            container=self.container,
            source='https://commons.wikimedia.org/wiki/File:Big_Buck_Bunny_extract.ogv',
            dest='/bunny',
        )

    def test_remote_mounts_form(self):
        """Test the remote mounts inline form"""
        self.login_and_redirect(
            self.superuser,
            reverse(
                'containers:update',
                kwargs={
                    'container': str(self.container.sodar_uuid),
                },
            ),
        )
        formsets = self.selenium.find_elements(
            By.CLASS_NAME, 'kiosc-remote-mount-form'
        )
        # One formset is visible initially
        self.assertTrue(formsets[0].is_displayed())
        for i in range(1, len(formsets)):
            self.assertFalse(formsets[i].is_displayed())


class TestReverseProxyView(UITestBase):
    def setUp(self):
        super().setUp()
        build_testdata_container(self.cli, 'sample-app-server')
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-server',
            tag='testing',
            container_port=80,
            host_port=14809,
            container_id=None,
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
        self.login_and_redirect_to_container(self.superuser, self.container)
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

        # This check is very unstable in CI
        # WebDriverWait(self.selenium, self.wait_time).until(
        #     ec.presence_of_element_located(
        #         (By.XPATH, '//h1[contains(text(), "Hello World")]')
        #     )
        # )
