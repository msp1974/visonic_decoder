"""Handles listening ports for clients to connect to."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import datetime as dt
import logging
from socket import AF_INET

from .protocol import ConnectionProtocol

_LOGGER = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    """Class to hold client connections."""

    transport: asyncio.Transport
    last_received_message: dt.datetime | None = None
    last_sent_message: dt.datetime | None = None


class ServerConnection:
    """Handles device connecting to us."""

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        received_message_callback: Callable,
        connected_callback: Callable = None,
        disconnected_callback: Callable = None,
        keep_alive_callback: Callable = None,
        run_watchdog: bool = False,
    ):
        """Init."""
        self.loop = asyncio.get_running_loop()
        self.name = name
        self.host = host
        self.port = port

        self.cb_received = received_message_callback
        self.cb_connected = connected_callback
        self.cb_disconnected = disconnected_callback

        self.server = None
        self.clients: dict[str, ClientConnection] = {}

    @property
    def client_count(self):
        """Get count of clients"""
        return len(self.clients.keys())

    def get_client_id(self, transport: asyncio.Transport) -> str:
        """Generate client_id."""
        return f"P{transport.get_extra_info('peername')[1]}"

    def get_transport(self, client_id: str) -> asyncio.Transport | None:
        """Get client transport."""
        try:
            return self.clients[client_id].transport
        except KeyError:
            return None

    async def start_listening(self):
        """Start server to allow Alarm to connect."""
        self.server = await self.loop.create_server(
            lambda: ConnectionProtocol(
                self.name,
                self.client_connected,
                self.client_disconnected,
                self.data_received,
            ),
            self.host,
            self.port,
            family=AF_INET,
        )
        _LOGGER.info(
            "Listening for %s connection on %s port %s", self.name, self.host, self.port
        )

    def client_connected(self, transport: asyncio.Transport):
        """Connected callback."""

        # Add client to clients tracker
        client_id = self.get_client_id(transport)
        self.clients[client_id] = ClientConnection(transport, dt.datetime.now())

        _LOGGER.info(
            "Client connected to %s %s server. Clients: %s",
            self.name,
            client_id,
            len(self.clients),
        )
        _LOGGER.debug("Connections: %s", self.clients)

        if self.cb_connected:
            self.cb_connected(self.name, client_id)

    def data_received(self, transport: asyncio.Transport, data: bytes):
        """Callback for when data received."""

        client_id = self.get_client_id(transport)

        # Update client last received
        self.clients[client_id].last_received_message = dt.datetime.now()

        # Send message to coordinator callback
        if self.cb_received:
            self.cb_received(self.name, client_id, data)

    def send_message(self, client_id: str, data: bytes) -> bool:
        """Send data over transport."""
        if client_id not in self.clients:
            client_id = list(self.clients.keys())[0]

        transport = self.get_transport(client_id)

        if transport:
            transport.write(data)
            _LOGGER.debug("Sent message via %s connection\n", client_id)

            # Update client last sent
            self.clients[client_id].last_sent_message = dt.datetime.now()

            return True
        _LOGGER.error("Cannot send message to %s.  Not connected\n", client_id)
        return False

    def client_disconnected(self, transport: asyncio.Transport):
        """Disconnected callback."""
        client_id = self.get_client_id(transport)
        _LOGGER.info(
            "Client disconnected from %s %s",
            self.name,
            client_id,
        )

        # Remove client id from list of clients
        try:
            del self.clients[client_id]
        except KeyError:
            _LOGGER.error(
                "Client does not exist trying to remove client form client list"
            )

        _LOGGER.debug("Clients remaining: %s. %s", len(self.clients), self.clients)

        if self.cb_disconnected:
            self.cb_disconnected(self.name, client_id)

    def disconnect_client(self, client_id: str):
        """Disconnect client."""
        transport = self.get_transport(client_id)
        if transport:
            if transport.can_write_eof():
                transport.write_eof()
            transport.close()

    async def shutdown(self):
        """Disconect the server."""

        for client_id in self.clients:
            _LOGGER.info("Disconnecting from %s %s", self.name, client_id)
            self.disconnect_client(client_id)
        self.server.close()
        await self.server.wait_closed()

