"""Django Channel consumers (for forwarding data only)."""

from asgiref.sync import async_to_sync
import itertools
import docker
import json
import logging
import struct
from channels.generic.websocket import WebsocketConsumer
import websocket
import threading
from typing import Optional
from urllib3.exceptions import ReadTimeoutError
import urllib3.contrib
import socket

from django.conf import settings
from .models import Container

from containers.models import (
    STATE_INITIAL,
    STATE_PULLING,
    STATE_TERMINATED,
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
    """Setup tunnel to the websocket behind the proxy."""

    debug = False

    def connect(self):
        """On connecting the consumer, create internal connection to tunnel target."""
        self._connect_next()
        self.accept()

    def _connect_next(self):
        """Create web socket to the tunnel/proxy target."""
        # TODO: check project permissions for users
        # Get DockerApp information for querying the port information.
        container = Container.objects.get(
            sodar_uuid=self.scope['url_route']['kwargs']['container'],
        )

        # Create web socket for writing data from inernal web socket to original client.
        def on_message(ws, message):
            """Forward any data from the client web socket to the orignal client."""
            self.send(message)

        websocket.enableTrace(self.debug)

        if settings.KIOSC_NETWORK_MODE == 'docker-shared':
            ws_url = 'ws://%s:%d/%s' % (
                container.container_id[:12],
                container.container_port,
                self.scope['url_route']['kwargs']['path'],
            )
        else:
            ws_url = 'ws://localhost:%d/%s' % (
                container.host_port,
                self.scope['url_route']['kwargs']['path'],
            )

        self.ws = websocket.WebSocketApp(ws_url, on_message=on_message)

        # Kick off thread copying data from internal web socket to the original client.
        thread = threading.Thread(
            target=self.ws.run_forever, args=(), daemon=True
        )
        thread.daemon = True
        thread.start()

    def disconnect(self, close_code):
        """On disconnecting, disconnect the internal web socket."""
        self.ws.close()

    def receive(self, text_data=None, bytes_data=None):
        """Forward any text and binary data to the internal web socket."""
        if text_data:
            self.ws.send(text_data)
        if bytes_data:
            self.ws.send(bytes_data)


class LogWatcherConsumer(WebsocketConsumer):
    """Setup tunnel to the websocket behind the proxy.

    Protocol:
    1a. The client (web browser) sends a websocket connection to this view:

        const socket = new WebSocket("https://kiosc.org/log-watcher");

    1b. We verify user authorization and accept the connection. We immediately
        send any existing ContainerLogEntries to the client. We also start
        receiving and forwarding additional log entries in real time through
        a Channel Layer.
    2.  We periodically send messages regarding the state of the container
    3a. The client sends a message with the amount of log lines they want:

        socket.send(1000)

        This is only accepted if the container is running, otherwise it's
        ignored. Ideally, the client will wait until a "running" status message
        from us before sending this message.
    3b. We start a thread that fetches the latest 1000 logs and starts streaming
        the logs from that moment onwards.
    4a. The client receives the lines and is supposed to print them.
    4b. If the client sends another message, we repeat the cycle from 2a.
    5a. The client closes the browser or refreshes the page, closing the
        websocket.
    5b. We kill the threads for logs watching and state polling.
    """

    def _watch_logs(self, tail: int):
        """
        Stream docker logs and send them throug the websocket as they occur.

        This function is inspired by
        docker.api.client._multiplexed_response_stream_helper(), except that it
        doesn't block, allowing us to gracefully kill the thread with an Event.
        The original method also disables socket timeout, but in our case we
        need it to prevent blocking.
        """
        cli = connect_docker(timeout=5)
        try:
            logs_generator = cli.logs(
                self.container.container_id,
                tail=tail,
                stream=True,
                follow=True,
                timestamps=True,
            )
        except docker.errors.NullResource as ex:
            if self.container.state not in (STATE_INITIAL, STATE_PULLING, STATE_FAILED):
                # This is likely a bug
                logger.error('Cannot fetch logs: %s', ex)
            # The container is not running
            return
        except docker.errors.APIError as ex:
            msg = {
                'type': 'container_rt_logs',
                'text': f'Cannot fetch logs: {ex}\n',
            }
            self.send(json.dumps(msg))
            return
        res = logs_generator._response
        while not self.logs_signal.wait(1):
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
                        raise ValueError(
                            'No data from docker log stream socket'
                        )
                    if self.logs_signal.is_set():
                        # Check if thread was killed during socket timeout.
                        break
                    msg = {
                        'type': 'container_rt_logs',
                        'text': data.decode('utf-8'),
                    }
                    self.send(json.dumps(msg))
            except ReadTimeoutError:
                # This is totally normal and prevents the socket from blocking.
                continue

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

    def _poll_state(self, interval_seconds=2):
        cli = connect_docker(timeout=5)
        while True:
            self.container.refresh_from_db()
            if self.container.state == STATE_INITIAL:
                msg = {
                    'type': 'container_state',
                    'state': STATE_INITIAL,
                    'text': 'The container is not running yet, please start it.',
                }
                self.send(json.dumps(msg))
            elif self.container.state == STATE_PULLING:
                msg = {
                    'type': 'container_state',
                    'state': STATE_PULLING,
                    'text': 'The container is being pulled, please be patient.',
                }
                self.send(json.dumps(msg))
            elif self.container.state == STATE_TERMINATED:
                msg = {
                    'type': 'container_state',
                    'state': STATE_TERMINATED,
                    'text': 'The container was stopped due to inactivity, please start it again.',
                }
                self.send(json.dumps(msg))
            elif not self.container.container_id:
                msg = {
                    'type': 'container_state',
                    'state': 'NOT_EXISTING',
                    'text': 'Something went wrong, please restart the container.',
                }
                self.send(json.dumps(msg))
            else:
                try:
                    instance = cli.inspect_container(
                        self.container.container_id
                    )
                    state = instance.get('State', {}).get('Status')
                    msg = {
                        'type': 'container_state',
                        'state': state,
                        'text': f'The container is {state}.',
                    }
                    self.send(json.dumps(msg))
                except docker.errors.APIError as ex:
                    logger.error(
                        '%s: %s (state is %s)',
                        self.container.sodar_uuid,
                        ex,
                        self.container.state,
                    )
                    msg = {
                        'type': 'container_state',
                        'state': 'DOCKER_API_ERROR',
                        'text': 'Something went wrong, please restart the container.',
                    }
                    self.send(json.dumps(msg))
            if self.state_signal.wait(interval_seconds):
                break

    def start_logs_watching(self, tail: int):
        """Start a thread to monitor the logs"""
        self.logs_signal.clear()
        self.logs_task = threading.Thread(
            target=self._watch_logs, args=(tail,), daemon=True
        )
        self.logs_task.start()
        logger.info(f'{self.__class__.__name__} logs thread started.')

    def start_state_polling(self):
        """Start a thread to monitor the container state"""
        self.state_signal.clear()
        self.state_task = threading.Thread(target=self._poll_state, daemon=True)
        self.state_task.start()
        logger.info(f'{self.__class__.__name__} state thread started.')

    def stop_logs_watching(self):
        """Kill the thread that monitors the logs"""
        self.logs_signal.set()
        try:
            self.logs_task.join()
            logger.info(f'{self.__class__.__name__} logs thread terminated.')
        except (AttributeError, RuntimeError):
            logger.debug(
                f'{self.__class__.__name__} disconnection before thread start.'
            )

    def stop_state_polling(self):
        """Kill the thread that monitors the state"""
        self.state_signal.set()
        try:
            self.state_task.join()
            logger.info(f'{self.__class__.__name__} state thread terminated.')
        except (AttributeError, RuntimeError):
            logger.debug(
                f'{self.__class__.__name__} disconnection before thread start.'
            )

    def connect(self):
        """Called upon websocket connect events

        This consumer can receive messages from the Channel Layer
        (https://channels.readthedocs.io/en/latest/topics/channel_layers.html).
        It belongs to a group named with the corresponding container sodar_uuid.
        """
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
        self.logs_signal = threading.Event()
        self.logs_task = None
        self.state_signal = threading.Event()
        self.state_task = None
        self.accept()
        if not user.has_perm(
            'containers.view_container', self.container.project
        ):
            self.close(code=4403, reason='Forbidden')
            return

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
        self.stop_logs_watching()
        self.stop_state_polling()

    def receive(
        self,
        text_data: Optional[str] = None,
        bytes_data: Optional[bytes] = None,
    ):
        """Called upon message received from the websocket

        Right now, the only case this happens is when the client wants to start
        watching logs or changing the number of log lines. Thus, we can assume
        that text_data contains the number of log lines.
        """
        print('===========')
        print(text_data)
        if text_data == 'HELO':
            # Start receiving new log entries in real time
            async_to_sync(self.channel_layer.group_add)(
                str(self.container.sodar_uuid), self.channel_name
            )
            # Send existing log entries
            for log_batch in batched(self.container.log_entries.all(), 1024):
                msg = {
                    'type': 'container_static_logs',
                    'text': '\n'.join(str(log_entry) for log_entry in log_batch),
                }
                self.send(json.dumps(msg))
            self.start_state_polling()
        else:
            self.stop_logs_watching()
            self.start_logs_watching(int(text_data))

    def container_task_message(self, event):
        # FIXME: make sure that we are done sending all static existing log entries (we could do this either in the client or here)
        msg = {'type': 'container_channel_logs', 'text': event['text']}
        self.send(json.dumps(msg))

    def container_pull_message(self, event):
        # FIXME: make sure that we are done sending all static existing log entries (we could do this either in the client or here)
        msg = {'type': 'container_pull_logs', 'status': event['status'], 'id': event.get('id')}
        self.send(json.dumps(msg))
