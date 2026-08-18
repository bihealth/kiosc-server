"""Test live container examples from the cookbook docs"""

import time
import docker

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from containers.models import (
    Container,
    ABSOLUTE_PATH_PROXY_PREFIX,
)
from containers.statemachines import connect_docker
from containers.tests.helpers import build_testdata_container, UITestBase
from containers.tests.factories import (
    ContainerFactory,
)


class TestLiveJupyter(UITestBase):
    """Test a Jupyter notebook example"""

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
        run_loc = (By.XPATH, '//div[@id="menu-panel"]//div[text()="Run"]')
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.element_to_be_clickable(run_loc)
        )
        self.selenium.find_element(*run_loc).click()
        time.sleep(1)
        run_loc = (By.XPATH, '//div[text()="Run All Cells"]')
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.element_to_be_clickable(run_loc)
        )
        self.selenium.find_element(*run_loc).click()
        time.sleep(1)
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.XPATH, '//div[text()="[1]:"]'))
        )
        print('element found')


class TestLiveSeaPiper(UITestBase):
    """Test a Seapiper example"""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.container = ContainerFactory(
            project=self.project,
            repository='sample-app-seapiper',
            tag='testing',
            container_port=8080,
            host_port=14023,
            container_id=None,
        )
        build_testdata_container(self.cli, 'sample-app-seapiper')

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

    def test_select_contrast(self):
        """Test the select input to choose the contrast"""
        self.login_and_redirect_to_container(self.superuser, self.container)
        table_id = 'DataTables_Table_0'
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element((By.ID, table_id), 'ENSG')
        )
        table_el = self.selenium.find_element(By.ID, table_id)
        table1 = table_el.text
        # Select another contrast
        self.selenium.find_element(
            By.CSS_SELECTOR, '#geneT-contrast + div .selectize-input'
        ).click()
        time.sleep(1)  # Wait for dropdown element to be rendered
        self.selenium.find_element(
            By.XPATH, '//div[@data-value="default::ICU_ID1"]'
        ).click()
        table_id = 'DataTables_Table_1'
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.text_to_be_present_in_element((By.ID, table_id), 'ENSG')
        )
        table_el = self.selenium.find_element(By.ID, table_id)
        # Check that the table's content changed
        self.assertNotEqual(table1, table_el.text)


class TestLiveCellXGene(UITestBase):
    """Test a CellXGene example"""

    def setUp(self):
        super().setUp()
        self.cli = connect_docker()
        self.container = ContainerFactory(
            project=self.project,
            repository='quay.io/biocontainers/cellxgene',
            tag='1.1.1--pyhdfd78af_0',
            container_port=8050,
            host_port=13124,
            container_id=None,
            command='cellxgene launch https://github.com/chanzuckerberg/cellxgene/raw/refs/heads/main/example-dataset/pbmc3k.h5ad -p 8050 --host 0.0.0.0 --verbose',
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

    def test_get_umap(self):
        """Test that we can see the UMAP plot"""
        self.login_and_redirect_to_container(self.superuser, self.container)
        # Enter the dataset name
        input_loc = (By.XPATH, '//input[@data-testid="new-annotation-name"]')
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.element_to_be_clickable(input_loc)
        )
        input_el = self.selenium.find_element(*input_loc)
        input_el.send_keys('kiosc_test\n')
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'embedding'))
        )
        self.assertEqual(
            self.selenium.find_element(By.ID, 'embedding').text,
            'umap: 2638 out of 2638 cells',
        )
        time.sleep(2)
