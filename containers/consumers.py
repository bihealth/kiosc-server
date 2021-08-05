"""Django Channel consumers (for forwarding data only)."""

from channels.generic.websocket import WebsocketConsumer
import websocket
import threading

from .models import Container, STATE_RUNNING


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
            sodar_uuid=self.scope["url_route"]["kwargs"]["container"],
            state=STATE_RUNNING,
        )

        # Create web socket for writing data from internal web socket to original client.
        def on_message(ws, message):
            """Forward any data from the client web socket to the orignal client."""
            self.send(message)

        websocket.enableTrace(self.debug)
        ws_url = "ws://127.0.0.1:%d/%s" % (
            container.host_port,
            self.scope["url_route"]["kwargs"]["path"],
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
