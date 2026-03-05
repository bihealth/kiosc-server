"""Django Channel consumers (for forwarding data only)."""

import docker
import logging
import struct
from channels.generic.websocket import WebsocketConsumer
import websocket
import threading
from typing import Optional

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
        thread = threading.Thread(target=self.ws.run_forever, args=())
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
    """Setup tunnel to the websocket behind the proxy."""

    def _watch_logs(self, container_id, tail):
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
                while header := res.raw.read(
                    docker.constants.STREAM_HEADER_SIZE_BYTES
                ):
                    _, length = struct.unpack(">BxxxL", header)
                    if not length:
                        continue
                    data = res.raw.read(length)
                    if not data:
                        break
                    self.send(data.decode("utf-8"))
            except Exception as ex:
                print("TIMED OUT ", type(ex), ex)

    def start_watching(self, tail):
        self.event.clear()
        self.task = threading.Thread(
            target=self._watch_logs,
            args=(self.container_id, tail),
        )
        self.task.start()
        logger.info(f"{self.__class__.__name__} thread started.")

    def stop_watching(self):
        self.event.set()
        if self.task is not None:
            self.task.join()
            logger.info(f"{self.__class__.__name__} thread terminated.")

    def connect(self):
        user = self.scope["user"]
        container_sodar_uuid = self.scope["url_route"]["kwargs"]["container"]
        container_obj = Container.objects.get(sodar_uuid=container_sodar_uuid)
        logger.info(
            f"New connection request to {self.__class__.__name__} for {container_sodar_uuid} from {user.username}"
        )
        self.container_id = container_obj.container_id
        self.event = threading.Event()
        self.task = None
        if not user.has_perm(
            "containers.view_container", container_obj.project
        ):
            self.close(code=403, reason="Forbidden")
            return
        if not self.container_id:
            self.close(code=404, reason="Container not running")
            return
        self.accept()

    def disconnect(self, close_code: int):
        self.stop_watching()

    def receive(
        self,
        text_data: Optional[str] = None,
        bytes_data: Optional[bytes] = None,
    ):
        self.stop_watching()
        self.start_watching(int(text_data))
