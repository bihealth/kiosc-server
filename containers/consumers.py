"""Django Channel consumers."""

from asgiref.sync import async_to_sync
import itertools
import docker
import json
import logging
import struct
from channels.generic.websocket import WebsocketConsumer
from datetime import datetime
import websocket
import threading
from typing import Optional
import requests
from urllib3.exceptions import ReadTimeoutError
import urllib3.contrib
import socket

from django.conf import settings
from django.db import connection
from django.urls import reverse
from .models import Container

from containers.models import (
    STATE_INITIAL,
    STATE_PULLING,
    STATE_DELETED,
    STATE_TERMINATED,
    STATE_CREATED,
    STATE_FAILED,
)
from containers.statemachines import connect_docker


logger = logging.getLogger(__name__)


# https://docs.python.org/3.12/library/itertools.html#itertools.batched
# itertools.batched() is only available in Python 3.12
def batched(iterable, n):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        yield batch


class TunnelConsumer(WebsocketConsumer):
    """Setup tunnel to the websocket behind the proxy.

    Establishes a tunnel for websockets that try to reach the Kiosc
    server from a web app.
    """

    debug = settings.DEBUG

    def connect(self):
        """Upon connect, create internal web socket to tunnel target."""
        # Get DockerApp information for querying the port information.
        user = self.scope['user']
        container = Container.objects.get(
            sodar_uuid=self.scope['url_route']['kwargs']['container'],
        )
        if not user.has_perm('containers.view_container', container.project):
            self.close(code=4403, reason='Forbidden')
            return

        # HACK: some servers, such as Jupyter, use absolute URLs. We set up a
        # convention: if the container_path starts with the absolute URL of
        # the container proxy, we forward the absolute path as is to the app.
        # The app must then be set up with this absolute base URL.
        # See https://github.com/bihealth/kiosc-server/issues/271
        path = self.scope['url_route']['kwargs']['path']
        if container.container_path.startswith(
            reverse(
                'containers:proxy',
                kwargs={'container': container.sodar_uuid, 'path': ''},
            )
        ):
            path = reverse(
                'containers:proxy',
                kwargs={'container': container.sodar_uuid, 'path': path},
            )[1:]

        # Create web socket for writing data from inernal web socket to original client.
        def on_message(ws, message):
            """Forward any data from the client web socket to the orignal client."""
            logger.debug('TunnelConsumer MESSAGE: %s', message)
            self.send(message)

        def on_error(ws, err):
            logger.debug('TunnelConsumer ERROR: %s', err)

        def on_close(ws, code, msg):
            logger.debug('TunnelConsumer CLOSED: %s (%s)', code, msg)

        websocket.enableTrace(self.debug)

        if settings.KIOSC_NETWORK_MODE == 'docker-shared':
            ws_url = 'ws://%s:%d/%s' % (
                container.container_id[:12],
                container.container_port,
                path,
            )
        else:
            ws_url = 'ws://localhost:%d/%s' % (
                container.host_port,
                path,
            )
        if query_string := self.scope['query_string']:
            ws_url += '?' + query_string.decode('utf8')

        self.ws = websocket.WebSocketApp(
            ws_url, on_message=on_message, on_error=on_error, on_close=on_close
        )

        # Kick off thread copying data from internal web socket to the original client.
        thread = threading.Thread(
            target=self.ws.run_forever,
            args=(),
            kwargs={'suppress_origin': True},
            daemon=True,
        )
        thread.start()
        self.accept()

    def disconnect(self, close_code):
        """On disconnecting, disconnect the internal web socket."""
        self.ws.close()

    def receive(self, text_data=None, bytes_data=None):
        """Forward any text and binary data to the internal web socket."""
        if text_data:
            self.ws.send(text_data)
        if bytes_data:
            self.ws.send(bytes_data)


class ContainerWatcherConsumer(WebsocketConsumer):
    """Monitors the status and logs of a container in real time.

    Protocol:
    1a. The client (web browser) sends a websocket connection to this view:

        const socket = new WebSocket("https://kiosc.org/log-watcher");

    1b. We verify user authorization and accept the connection.

    2a. The client reacts to the "open" event and sends its configuration:
        currently just the number of log lines it wants.

        socket.send(1000)

    2b. We immediately send any existing ContainerLogEntries from the db to the
        client (limited by the number of log lines requested). Then, we start
        receiving additional entries from the Django Channels layer, and forward
        them to the client. Then, we start a thread that periodically receives
        or polls content from the Docker daemon, and forward this content to the
        client.

    3a. The client receives the lines and is supposed to print them. In summary,
        these are the supported message types:
        - static_logs (from the db)
        - channel_logs (from the channel layer, in a task)
        - pull_logs (from the channel layer, in a pulling task)
        - daemon_logs (from the daemon)
        - container_state (from the daemon)
        - watcher_error (typically api error or unexplainable null resource)
    3b. If we receive another message from the client, we repeat from 2a.

    4a. The client closes the browser or refreshes the page, closing the
        websocket.
    4b. We kill the thread.
    """

    @classmethod
    def _get_state(cls, container: Container, cli: docker.APIClient) -> dict:
        """Returns the state of the container."""
        container.refresh_from_db()
        container_state = container.state
        container_id = container.container_id
        if container_state == STATE_INITIAL:
            return {
                'type': 'container_state',
                'state': STATE_INITIAL,
                'text': 'The container is not running yet, please start it.',
            }
        elif container_state == STATE_PULLING:
            return {
                'type': 'container_state',
                'state': STATE_PULLING,
                'text': 'The container is being pulled, please be patient.',
            }
        elif container_state == STATE_TERMINATED:
            return {
                'type': 'container_state',
                'state': STATE_TERMINATED,
                'text': 'The container was terminated due to inactivity, please start it again.',
            }
        elif container_state == STATE_CREATED:
            return {
                'type': 'container_state',
                'state': STATE_CREATED,
                'text': 'The container failed to start, please check the logs, update the config if necessary, and start it again.',
            }
        elif container_state == STATE_DELETED:
            return {
                'type': 'container_state',
                'state': STATE_DELETED,
                'text': 'The container was just updated or deleted, please start it again.',
            }
        elif not container_id:
            logger.error(
                'Cannot poll state for %s in state %s: %s',
                container.sodar_uuid,
                container_state,
                'Container id is None',
            )
            return {
                'type': 'container_state',
                'state': f'{container_state} (NOT_EXISTING)',
                'text': 'Something went wrong, please reset the container.',
            }
        else:
            try:
                instance = cli.inspect_container(container_id)
                state = instance.get('State', {}).get('Status')
                return {
                    'type': 'container_state',
                    'state': state,
                    'text': f'The container is {state}.',
                }
            except docker.errors.APIError as ex:
                logger.error(
                    '%s: %s (state is %s)',
                    container.sodar_uuid,
                    ex,
                    container.state,
                )
                return {
                    'type': 'container_state',
                    'state': 'DOCKER_API_ERROR',
                    'text': 'Something went wrong, please reset the container.',
                }

    def _send_logs(self, res: requests.models.Response):
        """
        Stream logs from the Docker daemon socket.

        Here, unlike with _get_logs(), we send messages in a loop because if
        there are multiple messages in the queue we want to deliver them all at
        once. This also means that if the logs keep coming within the socket
        timeout, this loop will never stop and the state will not be checked.
        However, it is OK because if the logs are coming it means that the
        container is still running.
        """
        try:
            # Header can be either empty or a byte string or a
            # ReadTimeoutError exception.
            while header := res.raw.read(
                docker.constants.STREAM_HEADER_SIZE_BYTES
            ):
                # If we are here, it means that the header is not empty.
                # Decode the content length as int.
                _, length = struct.unpack('>BxxxL', header)
                if not length:
                    break
                data = res.raw.read(length)
                if not data:
                    # Something terrible happened.
                    raise ValueError('No data from docker log stream socket')
                if self.watch_signal.is_set():
                    # Check if thread was killed during socket timeout.
                    break
                msg = {
                    'type': 'daemon_logs',
                    'text': data.decode('utf-8'),
                }
                self.send(json.dumps(msg))
        except ReadTimeoutError:
            # This is totally normal and prevents the socket from blocking.
            pass

    def _watch(self, tail: int):
        """
        Stream docker logs and send them throug the websocket as they occur.

        This function is inspired by
        docker.api.client._multiplexed_response_stream_helper(), except
        that it doesn't block, allowing us to gracefully kill the thread
        with an Event. The original method also disables socket timeout,
        but in our case we need it to prevent blocking. The default timeout
        is too long, so we set it to 1 second here. As per the docs of
        docker.api.client._disable_socket_timeout(), "Depending on the
        combination of python version and whether we're connecting over http or
        https, we might need to access _sock, which may or may not exist; or we
        may need to just settimeout on socket itself, which also may or may not
        have settimeout on it. To avoid missing the correct one, we try both."
        """
        cli = connect_docker()
        # This outer loop is used to check the container state if the logs
        # are not available.
        while not self.watch_signal.wait(4):
            try:
                # Send a status update immediately
                msg = self._get_state(self.container, cli)
                self.send(json.dumps(msg))

                logs_generator = cli.logs(
                    self.container.container_id,
                    tail=tail,
                    stream=True,
                    follow=True,
                    timestamps=True,
                )
                res = logs_generator._response
                sock = cli._get_raw_response_socket(res)
                socks = [sock, getattr(sock, '_sock', None)]
                for s in socks:
                    if not hasattr(s, 'settimeout'):
                        continue
                    s.settimeout(8)

                # Send logs immediately, if available
                self._send_logs(res)

                # If the logs are available, we enter this inner loop
                while not self.watch_signal.wait(4):
                    # First we send a status update
                    msg = self._get_state(self.container, cli)
                    self.send(json.dumps(msg))
                    # Then we keep sending logs as long as they keep coming.
                    # If there are no logs within the socket timeout, we go
                    # back and send a status update, then wait for logs, and
                    # so on.
                    self._send_logs(res)

                # Close the socket (see docker.types.daemon.CancellableStream())
                if not res.raw.closed:
                    # find the underlying socket object
                    # based on api.client._get_raw_response_socket
                    sock_fp = res.raw._fp.fp
                    if hasattr(sock_fp, 'raw'):
                        sock_raw = sock_fp.raw
                        if hasattr(sock_raw, 'sock'):
                            sock = sock_raw.sock
                        elif hasattr(sock_raw, '_sock'):
                            sock = sock_raw._sock
                    else:
                        sock = sock_fp._sock
                    if hasattr(urllib3.contrib, 'pyopenssl') and isinstance(
                        sock, urllib3.contrib.pyopenssl.WrappedSocket
                    ):
                        sock = sock.socket
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()

            except docker.errors.NullResource as ex:
                if self.container.state not in (
                    STATE_INITIAL,
                    STATE_PULLING,
                    STATE_FAILED,
                    STATE_DELETED,
                ):
                    # This is likely a bug, we quit
                    logger.error(
                        'Cannot fetch logs for %s in state %s: %s',
                        self.container.sodar_uuid,
                        self.container.state,
                        ex,
                    )
                    msg = {
                        'type': 'watcher_error',
                        'text': 'Cannot fetch logs '
                        f'(state is {self.container.state}): {ex}\n',
                    }
                    self.send(json.dumps(msg))
                    break
                # Actually we also send an empty logs message to clear the
                # initial "Loading" text.
                msg = {
                    'type': 'daemon_logs',
                    'text': '',
                }
                self.send(json.dumps(msg))
                continue
            except docker.errors.APIError as ex:
                # This is likely a bug, we quit
                logger.error(
                    'Cannot fetch logs for %s in state %s: %s',
                    self.container.sodar_uuid,
                    self.container.state,
                    ex,
                )
                msg = {
                    'type': 'watcher_error',
                    'text': 'Cannot fetch logs '
                    f'(state is {self.container.state}): {ex}\n',
                }
                self.send(json.dumps(msg))
                break

        # Close Django connections to the db from this thread
        # https://stackoverflow.com/questions/44802617/database-is-being-accessed-by-other-users-error-when-using-threadpoolexecutor
        connection.close()

    def _start_watching(self, tail: int):
        """Start a thread to monitor the container state"""
        self.watch_signal.clear()
        self.watch_task = threading.Thread(
            target=self._watch, args=(tail,), daemon=True
        )
        self.watch_task.start()
        logger.info(f'{self.__class__.__name__} state thread started.')

    def _stop_watching(self):
        """Kill the thread that monitors the state"""
        self.watch_signal.set()
        try:
            self.watch_task.join()
            logger.info(f'{self.__class__.__name__} state thread terminated.')
        except (AttributeError, RuntimeError):
            logger.debug(
                f'{self.__class__.__name__} disconnection before thread start.'
            )

    def connect(self):
        user = self.scope['user']
        container_sodar_uuid = self.scope['url_route']['kwargs']['container']
        self.container = Container.objects.get(sodar_uuid=container_sodar_uuid)
        logger.info(
            f'New connection request to {self.__class__.__name__} '
            f'for {container_sodar_uuid} from {user.username}'
        )
        logger.debug(
            'Currently active threads: %s',
            [thread.name for thread in threading.enumerate()],
        )
        self.watch_signal = threading.Event()
        self.watch_task = None
        if not user.has_perm(
            'containers.view_container', self.container.project
        ):
            self.close(code=4403, reason='Forbidden')
            return
        self.accept()

    def disconnect(self, close_code: int):
        """Called upon websocket disconnect events"""
        user = self.scope['user']
        container_sodar_uuid = self.scope['url_route']['kwargs']['container']
        logger.info(
            f'{self.__class__.__name__} disconnection request for '
            f'{container_sodar_uuid} from {user.username}'
        )
        async_to_sync(self.channel_layer.group_discard)(
            container_sodar_uuid, self.channel_name
        )
        self._stop_watching()

    def receive(
        self,
        text_data: Optional[str] = None,
        bytes_data: Optional[bytes] = None,
    ):
        """Called upon message received from the websocket"""
        if not text_data.isnumeric():
            self.disconnect(4422)
        logs_tail = int(text_data)
        # Start receiving new log entries in real time from the channel layer
        async_to_sync(self.channel_layer.group_add)(
            str(self.container.sodar_uuid), self.channel_name
        )
        # Send existing log entries from the db, batched for efficiency
        for log_batch in batched(
            self.container.log_entries.order_by('date_created').all()[
                :logs_tail
            ],
            1024,
        ):
            msg = {
                'type': 'static_logs',
                'text': ''.join(str(log_entry) for log_entry in log_batch),
            }
            self.send(json.dumps(msg))
        if self.watch_task:
            self._stop_watching()
        self._start_watching(logs_tail)

    def container_task_message(self, event: dict):
        """Send a real-time message from the statemachine task.

        This function is called by the Django channels layer.
        """
        # FIXME: make sure that we are done sending all static existing
        # log entries (we could do this either in the client or here)
        msg = {
            'type': 'channel_logs',
            'text': '{} [Kiosc Task] {}'.format(
                datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f000Z'),
                event['text'],
            ),
        }
        self.send(json.dumps(msg))

    def container_pull_message(self, event: dict):
        """Send a real-time message from the statemachine pulling task.

        This function is called by the Django channels layer.
        """
        # FIXME: make sure that we are done sending all static existing
        # log entries (we could do this either in the client or here)
        msg = {
            'type': 'pull_logs',
            'status': event['status'],
            'id': event.get('id'),
        }
        self.send(json.dumps(msg))
