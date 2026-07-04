"""Tests for the custom Docker registry"""

import base64
import urllib3

from django.conf import settings
from django.urls import reverse

from containers.models import Container
from containers.tests.factories import ProjectFactory
from containers.tests.helpers import TestBase

from projectroles.models import RoleAssignment
from projectroles.constants import SODAR_CONSTANTS


class TestKioscRegistryProxyView(TestBase):
    """Test the view that proxies requests to the custom registry"""

    def test_missing_auth_header(self):
        """Test registry proxy with missing authorization header"""
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': '',
                },
            ),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.content,
            b'{"errors": [{"code": "UNAUTHORIZED", "message": "Please provide the Authorization header.", "detail": null}]}',
        )
        self.assertEqual(
            response.headers['Docker-Distribution-Api-Version'], 'registry/2.0'
        )

    def test_wrong_auth_type(self):
        """Test registry proxy with wrong authentication type"""
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': '',
                },
            ),
            headers={'Authorization': 'MischievousScheme bad-actor-params'},
        )
        self.assertEqual(response.status_code, 401)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'UNAUTHORIZED')

    def test_wrong_auth_params(self):
        """Test registry proxy with wrong authentication parameters"""
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': '',
                },
            ),
            headers={'Authorization': 'Basic mumbojumbo'},
        )
        self.assertEqual(response.status_code, 401)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'UNAUTHORIZED')

    def test_wrong_credentials(self):
        """Test registry proxy with wrong credentials"""
        creds = base64.b64encode(b'invalid:password').decode('ascii')
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': '',
                },
            ),
            headers={'Authorization': f'Basic {creds}'},
        )
        self.assertEqual(response.status_code, 401)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'UNAUTHORIZED')
        self.assertEqual(
            content['errors'][0]['message'], 'Invalid credentials.'
        )

    def test_invalid_tag(self):
        """Test registry proxy with invalid image tag (not a UUID)"""
        # Alice is a real user
        creds = base64.b64encode(b'alice:password').decode('ascii')
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': 'not-a-uuid/alpine:latest',
                },
            ),
            headers={'Authorization': f'Basic {creds}'},
        )
        self.assertEqual(response.status_code, 400)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'NAME_INVALID')

    def test_tag_not_a_project(self):
        """Test registry proxy with invalid image tag (not a project UUID)"""
        category = ProjectFactory(type=SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'])
        project = ProjectFactory(parent=category)
        self.role_owner_as = RoleAssignment.objects.create(
            project=project, user=self.user, role=self.role_owner
        )
        # Alice is self.user
        creds = base64.b64encode(b'alice:password').decode('ascii')
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': f'{category.sodar_uuid}/alpine:latest',
                },
            ),
            headers={'Authorization': f'Basic {creds}'},
        )
        self.assertEqual(response.status_code, 400)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'NAME_INVALID')

    def test_no_permissions(self):
        """Test registry proxy with no permissions"""
        # Bob is a real user, but cannot create containers in self.project
        creds = base64.b64encode(b'bob:password').decode('ascii')
        response = self.client.get(
            reverse(
                'registry-proxy',
                kwargs={
                    'path': f'{self.project.sodar_uuid}/alpine:latest',
                },
            ),
            headers={'Authorization': f'Basic {creds}'},
        )
        self.assertEqual(response.status_code, 403)
        content = response.json()
        self.assertEqual(content['errors'][0]['code'], 'DENIED')

    def test_success(self):
        """Test registry proxy success"""
        # Alice is the project owner so she can create containers
        creds = base64.b64encode(b'alice:password').decode('ascii')
        # We expect the request to go through the proxy, but the registry will
        # not pick up the phone because it's not part of the testing environment
        with self.assertRaises(urllib3.exceptions.MaxRetryError):
            self.client.get(
                reverse(
                    'registry-proxy',
                    kwargs={
                        'path': f'{self.project.sodar_uuid}/alpine:latest',
                    },
                ),
                headers={'Authorization': f'Basic {creds}'},
            )


class TestKioscRegistryNotificationsView(TestBase):
    """Test the view receiving notifications from the custom registry"""

    def test_missing_auth_header(self):
        """Test registry notifications with missing authorization header"""
        response = self.client.post(
            reverse('containers:registry-notifications')
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_auth_type(self):
        """Test registry notifications with invalid authentication type"""
        response = self.client.post(
            reverse('containers:registry-notifications'),
            headers={'Authorization': 'Basic meowmeow'},
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_auth_token(self):
        """Test registry notifications with wrong authentication token"""
        response = self.client.post(
            reverse('containers:registry-notifications'),
            headers={'Authorization': 'Bearer meowmeow'},
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_payload(self):
        """Test registry notifications with invalid payload (not JSON)"""
        response = self.client.post(
            reverse('containers:registry-notifications'),
            body='string',
            headers={
                'Authorization': f'Bearer {settings.KIOSC_CUSTOM_REGISTRY_NOTIFICATIONS_TOKEN}'
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_payload_json(self):
        """Test registry notifications with invalid payload (wrong structure)"""
        response = self.client.post(
            reverse('containers:registry-notifications'),
            data={'invalid_key': 'bogus_value'},
            content_type='application/json',
            headers={
                'Authorization': f'Bearer {settings.KIOSC_CUSTOM_REGISTRY_NOTIFICATIONS_TOKEN}'
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_success(self):
        """Test registry notifications success"""
        self.assertEqual(
            Container.objects.filter(
                repository=f'{self.project.sodar_uuid}/alpine', tag='latest'
            ).count(),
            0,
        )
        response = self.client.post(
            reverse('containers:registry-notifications'),
            data={
                'events': [
                    {
                        'action': 'pull',
                    },
                    {
                        'action': 'push',
                        'target': {
                            'repository': f'{self.project.sodar_uuid}/alpine',
                            'tag': 'latest',
                        },
                        'actor': {
                            'name': 'alice',
                        },
                    },
                ]
            },
            content_type='application/json',
            headers={
                'Authorization': f'Bearer {settings.KIOSC_CUSTOM_REGISTRY_NOTIFICATIONS_TOKEN}'
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Container.objects.filter(
                repository=f'{self.project.sodar_uuid}/alpine', tag='latest'
            ).count(),
            1,
        )
