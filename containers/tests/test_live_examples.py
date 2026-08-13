"""Test live container examples from the docs"""

import time
import docker

from selenium.webdriver.common.by import By

from containers.models import (
    Container,
    ABSOLUTE_PATH_PROXY_PREFIX,
)
from containers.statemachines import connect_docker
from containers.tests.helpers import build_testdata_container, UITestBase
from containers.tests.factories import (
    ContainerFactory,
)


class TestLiveJupyter(
    UITestBase,
):
    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        build_testdata_container(self.cli, 'sample-app-jupyter')
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-jupyter',
            tag='testing',
            container_port=8888,
            host_port=12359,
            container_id=None,
            environment={'JUPYTER_BASE_URL': ABSOLUTE_PATH_PROXY_PREFIX},
            container_path=ABSOLUTE_PATH_PROXY_PREFIX
            + 'notebooks/my_notebook.ipynb',
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

    def test_get_notebook(self):
        """Test Jupyter container for get notebook"""
        self.login_and_redirect_to_container(self.superuser, self.container)
        time.sleep(10)
        run_all_button = self.selenium.find_element(
            By.XPATH,
            '//jp-button[@data-command="notebook:run-cell-and-select-next"]',
        )
        run_all_button.click()
        time.sleep(2)
        self.selenium.find_element(By.XPATH, '//div[text()="[1]:"]')
