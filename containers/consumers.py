"""Django Channel consumers (for forwarding data only)."""

import docker
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

from containers.statemachines import connect_docker


logger = logging.getLogger(__name__)


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

    1b. We verify user authorization and accept the connection.
    2a. The client sends a message with the amount of log lines they want:

        socket.send(1000)

    2b. We start a thread that fetches the latest 1000 logs and starts streaming
        the logs from that moment onwards.
    3a. The client receives the lines and is supposed to print them.
    3b. If the client sends another message, we repeat the cycle from 2a.
    4a. The client closes the browser or refreshes the page, closing the
        websocket.
    4b. We kill the thread.
    """

    def _watch_logs(self, container_id: str, tail: int):
        """
        Stream docker logs and send them throug the websocket as they occur.

        This function is inspired by
        docker.api.client._multiplexed_response_stream_helper(), except that it
        doesn't block, allowing us to gracefully kill the thread with an Event.
        The original method also disables socket timeout, but in our case we
        need it to prevent blocking.
        """
        cli = connect_docker(timeout=5)
        logs_generator = cli.logs(
            container_id, tail=tail, stream=True, follow=True, timestamps=True
        )
        res = logs_generator._response
        while not self.event.wait(1):
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
                    if self.event.is_set():
                        # Check if thread was killed during socket timeout.
                        break
                    self.send(data.decode('utf-8'))
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

    def start_watching(self, tail: int):
        """Start a thread to monitor the logs"""
        self.event.clear()
        self.task = threading.Thread(
            target=self._watch_logs, args=(self.container_id, tail), daemon=True
        )
        self.task.start()
        logger.info(f'{self.__class__.__name__} thread started.')

    def stop_watching(self):
        """Kill the thread that monitors the logs"""
        self.event.set()
        try:
            self.task.join()
            logger.info(f'{self.__class__.__name__} thread terminated.')
        except (AttributeError, RuntimeError):
            logger.debug(
                f'{self.__class__.__name__} disconnection before thread start.'
            )

    def connect(self):
        """Called upon websocket connect events"""
        user = self.scope['user']
        container_sodar_uuid = self.scope['url_route']['kwargs']['container']
        container_obj = Container.objects.get(sodar_uuid=container_sodar_uuid)
        logger.info(
            f'New connection request to {self.__class__.__name__} '
            f'for {container_sodar_uuid} from {user.username}'
        )
        logger.debug(
            'Currently active threads: %s',
            [thread.name for thread in threading.enumerate()],
        )
        self.container_id = container_obj.container_id
        self.event = threading.Event()
        self.task = None
        if not user.has_perm(
            'containers.view_container', container_obj.project
        ):
            self.close(code=403, reason='Forbidden')
            return
        if not self.container_id:
            self.close(code=404, reason='Container not running')
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
        self.stop_watching()

    def receive(
        self,
        text_data: Optional[str] = None,
        bytes_data: Optional[bytes] = None,
    ):
        """Called upon message received from the websocket"""
        self.stop_watching()
        self.start_watching(int(text_data))
