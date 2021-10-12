from test_plus.test import TestCase
from django.test import override_settings

from containers.serializers import ContainerSerializer


class TestContainerSerializer(TestCase):
    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_valid_mode_host(self):
        data = {
            "title": "some title",
            "repository": "some repos",
            "tag": "some tag",
            "host_port": 8080,
        }
        expected = {
            **data,
            "date_last_status_update": None,
            "image_id": None,
            "container_ip": None,
            "container_id": None,
            "container_path": None,
            "heartbeat_url": None,
            "environment": None,
            "environment_secret_keys": None,
            "command": None,
            "containertemplatesite": None,
            "containertemplateproject": None,
            "description": None,
        }
        serializer = ContainerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, expected)

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_invalid_mode_host_missing_host_port(self):
        data = {
            "title": "some title",
            "repository": "some repos",
            "tag": "some tag",
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("host_port" in serializer.errors)
        self.assertEqual(serializer.errors["host_port"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_invalid_mode_host_missing_title(self):
        data = {
            "repository": "some repos",
            "tag": "some tag",
            "host_port": 8080,
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("title" in serializer.errors)
        self.assertEqual(serializer.errors["title"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_invalid_mode_host_missing_repository(self):
        data = {
            "title": "some title",
            "tag": "some tag",
            "host_port": 8080,
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("repository" in serializer.errors)
        self.assertEqual(serializer.errors["repository"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="host")
    def test_invalid_mode_host_missing_tag(self):
        data = {
            "title": "some title",
            "repository": "some repos",
            "host_port": 8080,
        }

        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("tag" in serializer.errors)
        self.assertEqual(serializer.errors["tag"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_valid_mode_shared(self):
        data = {
            "title": "some title",
            "repository": "some repos",
            "tag": "some tag",
        }
        expected = {
            **data,
            "date_last_status_update": None,
            "image_id": None,
            "container_ip": None,
            "container_id": None,
            "container_path": None,
            "heartbeat_url": None,
            "host_port": None,
            "environment": None,
            "environment_secret_keys": None,
            "command": None,
            "containertemplatesite": None,
            "containertemplateproject": None,
            "description": None,
        }
        serializer = ContainerSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, expected)

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_invalid_mode_shared_missing_title(self):
        data = {
            "repository": "some repos",
            "tag": "some tag",
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("title" in serializer.errors)
        self.assertEqual(serializer.errors["title"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_invalid_mode_shared_missing_repository(self):
        data = {
            "title": "some title",
            "tag": "some tag",
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("repository" in serializer.errors)
        self.assertEqual(serializer.errors["repository"][0].code, "required")

    @override_settings(KIOSC_NETWORK_MODE="docker-shared")
    def test_invalid_mode_shared_missing_tag(self):
        data = {
            "title": "some title",
            "repository": "some repos",
        }
        serializer = ContainerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("tag" in serializer.errors)
        self.assertEqual(serializer.errors["tag"][0].code, "required")
