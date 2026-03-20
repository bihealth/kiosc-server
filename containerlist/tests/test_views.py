"""Tests for the containerlist views."""

from django.urls import reverse

from containers.tests.helpers import TestBase


class TestContainerSiteListView(TestBase):
    """Tests for ``ContainerListView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(reverse('containerlist:overview'))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['object_list']), 0)

    def test_get_one_container(self):
        self.create_one_container()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    'kioscadmin:overview',
                )
            )

            self.assertEqual(len(response.context['object_list']), 1)
            self.assertListEqual(
                list(response.context['object_list']), [self.container1]
            )
