"""Tests for the kioscadmin views."""

from unittest.mock import patch

from django.urls import reverse

from containers.tests.helpers import TestBase, DockerMock


class TestKioscAdminView(TestBase):
    """Tests for ``KioscAdminView``."""

    def test_get_success(self):
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["object_list"]), 0)

    @patch("docker.api.client.APIClient.networks")
    @patch("docker.api.client.APIClient.inspect_network")
    def test_get_networks(self, inspect_network, networks):
        networks.side_effect = [DockerMock.networks]
        inspect_network.side_effect = [DockerMock.inspect_network]

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            expected = [
                {
                    "name": DockerMock.inspect_network.get("Name"),
                    "id": DockerMock.inspect_network.get("Id"),
                    "driver": DockerMock.inspect_network.get("Driver"),
                    "subnet": DockerMock.inspect_network.get("IPAM")
                    .get("Config")[0]
                    .get("Subnet"),
                    "gateway": DockerMock.inspect_network.get("IPAM")
                    .get("Config")[0]
                    .get("Gateway"),
                    "containers": [
                        {
                            "id": list(
                                DockerMock.inspect_network.get(
                                    "Containers"
                                ).keys()
                            )[0],
                            "name": list(
                                DockerMock.inspect_network.get(
                                    "Containers"
                                ).values()
                            )[0].get("Name"),
                            "ip": list(
                                DockerMock.inspect_network.get(
                                    "Containers"
                                ).values()
                            )[0].get("IPv4Address"),
                        }
                    ],
                }
            ]

            self.assertEqual(len(response.context["networks"]), 1)
            self.assertEqual(response.context["networks"], expected)

    @patch("docker.api.client.APIClient.images")
    def test_get_images(self, images):
        images.side_effect = [DockerMock.images]

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            expected = [
                {
                    "id": DockerMock.images[0].get("Id"),
                    "repos": DockerMock.images[0].get("RepoTags")[0],
                }
            ]

            self.assertEqual(len(response.context["images"]), 1)
            self.assertEqual(response.context["images"], expected)

    @patch("docker.api.client.APIClient.volumes")
    def test_get_volumes(self, volumes):
        volumes.side_effect = [DockerMock.volumes]

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            expected = [
                {
                    "name": DockerMock.volumes.get("Volumes")[0].get("Name"),
                    "mountpoint": DockerMock.volumes.get("Volumes")[0].get(
                        "Mountpoint"
                    ),
                }
            ]

            self.assertEqual(len(response.context["volumes"]), 1)
            self.assertEqual(response.context["volumes"], expected)

    @patch("docker.api.client.APIClient.containers")
    def test_get_not_in_kiosc(self, containers):
        containers.side_effect = [DockerMock.containers]

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            expected = [
                {
                    "id": DockerMock.containers[0].get("Id"),
                    "name": DockerMock.containers[0]
                    .get("Names")[0]
                    .lstrip("/"),
                    "image": DockerMock.containers[0].get("Image"),
                }
            ]

            self.assertEqual(len(response.context["not_in_kiosc"]), 1)
            self.assertEqual(response.context["not_in_kiosc"], expected)

    def test_get_one_container(self):
        self.create_one_container()

        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    "kioscadmin:overview",
                )
            )

            self.assertEqual(len(response.context["object_list"]), 1)
            self.assertListEqual(
                list(response.context["object_list"]), [self.container1]
            )
