"""Views to interact with a container registry"""

import base64
import logging
import json
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views import View

from revproxy.views import ProxyView

from projectroles.models import Project

from containers.models import Container


logger = logging.getLogger(__name__)


class KioscRegistryMixin:
    """Mixin for private container registry operations"""

    def _resp_failure(
        self, status: int, code: str, message: str, detail: Optional[Any] = None
    ):
        """Respond with an error which the Docker client can understand

        The docker client expects standardized error messages from the
        registries when something goes wrong. Here is the full spec:
        https://docker-docs.uclv.cu/registry/spec/api/.

        We only need to implement messages that are Kiosc-specific. Successful
        requests are forwarded to the upstream registry, which can independenty
        raise additional errors.
        """
        response = JsonResponse(
            {
                'errors': [
                    {
                        'code': code,
                        'message': message,
                        'detail': detail,
                    }
                ]
            },
            status=status,
        )
        # This header must always be present
        response.setdefault('Docker-Distribution-Api-Version', 'registry/2.0')
        # This header is added for security
        response.setdefault('X-Content-Type-Options', '[nosniff]')
        # This header should be present only in authentication errors,
        # but it doesn't hurt to always include it
        response.setdefault(
            'WWW-Authenticate', 'Basic realm="KioscRegistry Realm"'
        )
        return response


class KioscRegistryProxyView(KioscRegistryMixin, ProxyView):
    """Proxy for Docker Registry requests

    Docker clients can connect to a custom registry behind kiosc. This view
    proxies all HTTP requests to the custom registry, after doing some
    authentication and business logic.

    References:

    - https://mirilittleme.medium.com/how-docker-login-works-under-the-hood-42225601843c
    - https://distribution.github.io/distribution/recipes/nginx/
    """

    upstream = settings.KIOSC_CUSTOM_REGISTRY_URL
    add_x_forwarded = True

    def dispatch(self, request, path):
        # Authenticate user
        if 'Authorization' not in request.headers:
            logger.warning(
                'Registry proxy error (missing Authorization header)'
            )
            return self._resp_failure(
                status=401,
                code='UNAUTHORIZED',
                message='Please provide the Authorization header.',
            )
        else:
            auth_header = request.headers['Authorization']
            try:
                assert auth_header.startswith('Basic ')
                creds = auth_header.removeprefix('Basic ').strip()
                username, password = (
                    base64.b64decode(creds).decode('ascii').split(':', 1)
                )
            except (AssertionError, ValueError):
                logger.warning(
                    'Registry proxy error (invalid Authorization header)'
                )
                return self._resp_failure(
                    status=401,
                    code='UNAUTHORIZED',
                    message='Invalid Authorization header.',
                )
            user = authenticate(request, username=username, password=password)
            if user is None:
                logger.warning('Registry proxy error (invalid credentials)')
                return self._resp_failure(
                    status=401,
                    code='UNAUTHORIZED',
                    message='Invalid credentials.',
                )
        # `docker login` requests only ask for the '/v2' path, while
        # `docker push` and `docker pull` ask for the image name after '/v2'.
        # The kiosc business rules should only apply to push and pull actions.
        if request.path.strip('/') != 'v2':
            # Business rule: image path must start with project's sodar_uuid
            project_uuid = path.split('/', 1)[0]
            try:
                project = Project.objects.get(sodar_uuid=project_uuid)
                assert project.is_project(), (
                    f'{project_uuid} is not a valid project'
                )
            except (
                Project.DoesNotExist,
                ValidationError,
                AssertionError,
            ) as ex:
                logger.warning(
                    'Registry proxy error (image is not tagged with '
                    'the project sodar_uuid): %s',
                    ex,
                )
                return self._resp_failure(
                    status=400,
                    code='NAME_INVALID',
                    message='Please tag the image as '
                    '<project sodar_uuid>/<image>.',
                )
            # User must have permission to create containers in this project
            if not user.has_perm('containers.create_container', project):
                logger.warning('Registry proxy error (not enough permissions)')
                return self._resp_failure(
                    status=403,
                    code='DENIED',
                    message='You cannot create containers in this project.',
                )
        # Proxy the request to the actual registry
        request.META['X_REAL_IP'] = request.META['REMOTE_ADDR']
        return super().dispatch(request, 'v2/' + path)


class KioscRegistryNotificationsView(View):
    """Listen to notifications from a container registry"""

    secret_token = settings.KIOSC_CUSTOM_REGISTRY_NOTIFICATIONS_TOKEN

    def post(self, request, *args, **kwargs):
        if 'Authorization' not in request.headers:
            logger.warning(
                'Registry notification error (missing Authorization header)'
            )
            return HttpResponse(status=401)
        else:
            auth_header = request.headers['Authorization']
            token = auth_header.removeprefix('Bearer ').strip()
            if token != self.secret_token:
                logger.warning(
                    'Registry notification error (invalid Bearer token)'
                )
                return HttpResponse(status=401)
        try:
            body = json.loads(request.body.decode('utf-8'))
            events = body['events']
            assert isinstance(events, list)
        except (json.decoder.JSONDecodeError, KeyError, AssertionError):
            logger.warning(
                'Registry notification error (malformed notification)'
            )
            return HttpResponse(status=400)
        for event in events:
            try:
                # We should get only push events as per the registry config,
                # but still, we double check here. We don't care about pulls.
                if event['action'] != 'push':
                    continue
                repository = event['target']['repository']
                project_uuid, image = repository.split('/', 1)
                tag = event['target']['tag']
                # XXX: Can we assume that the actor has a name field?
                actor = event['actor']['name']
                project = Project.objects.get(sodar_uuid=project_uuid)
                logger.info(
                    f'Registry notification: user "{actor}" just pushed '
                    f'{image}:{tag} for project "{project}" ({project_uuid})'
                )
                # Create a new container for the image which was just pushed
                Container.objects.get_or_create(
                    repository=repository,
                    tag=tag,
                    project=project,
                    title=image.title() + ':' + tag,
                )
            except Exception as ex:
                logger.error(
                    'Failed to create container from registry push (%s): %s',
                    str(ex),
                    event,
                )
        return HttpResponse()
