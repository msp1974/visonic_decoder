"""Message coordinator."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
import logging
from operator import attrgetter
import datetime as dt
import traceback

from .helpers import log_message

from .connections.manager import ConnectionManager, ConnectionProfile
from .const import (
    ConnectionName,
    MessagePriority,
    MessageType,
)
from .decoders.pl31_decoder import PowerLink31MessageDecoder
from .decoders.b0_message import (
    B0MessageDecoder,
    B0Response,
)
from .decoders.standard_message import STDMessageDecoder


_LOGGER = logging.getLogger(__name__)


class MessageCoordinatorStatus(StrEnum):
    """Message coordinator status Enum."""

    STOPPED = "stopped"
    RUNNING = "running"
    CLOSING = "closing"


@dataclass
class MessageTracker:
    """Tracker for messages."""

    last_message_no: int = 0
    last_message_timestamp: dt.datetime = 0

    def get_next(self):
        """Get next msg id."""
        return self.last_message_no + 1


class QueueID:
    """Queue message id generator."""

    _id: int = 0

    @staticmethod
    def get():
        """Get queue id."""
        QueueID._id += 1
        return QueueID._id


@dataclass
class QueuedMessage:
    """Queued message"""

    queue_id: int
    priority: MessagePriority = MessagePriority.LOW
    destination: ConnectionName | None = None
    client_id: str | None = None
    message: bytes = None


class MessageQueue:
    """Message queue."""

    def __init__(self):
        self._queue: list[QueuedMessage] = []
        self._queue_id = QueueID()
        self._last_id: int = 0

    @property
    def queue_length(self) -> int:
        """Get queue length."""
        return len(self._queue)

    def put(
        self,
        destination: ConnectionName,
        client_id: str,
        message: bytes,
        priority: MessagePriority = MessagePriority.LOW,
    ):
        """Put message on queue."""
        q_id = self._queue_id.get()
        self._queue.append(
            QueuedMessage(
                queue_id=q_id,
                priority=priority,
                destination=destination,
                client_id=client_id,
                message=message,
            )
        )

    def get(self) -> QueuedMessage:
        """Get message from queue."""
        if len(self._queue) > 0:
            prioritised_list = sorted(
                self._queue, key=attrgetter("priority", "queue_id")
            )
            msg = prioritised_list[0]
            self._last_id = msg.queue_id
            return msg.destination, msg.client_id, msg.message

    def processed(self):
        """Remove queued message from queue as now processed."""
        for idx, msg in enumerate(self._queue):
            if msg.queue_id == self._last_id:
                self._queue.pop(idx)
                return

    def clear(self):
        """Clear message queue."""
        self._queue = []


class MessageCoordinator:
    """Class for message coordinator

    Ensures flow control of Request -> ACK -> Response
    Ensures messages from one connection get routed to the right other connection
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        connection_profiles: list[ConnectionProfile],
    ):
        """Init."""
        self._loop = loop
        self.connection_profiles = connection_profiles

        self.status: MessageCoordinatorStatus = MessageCoordinatorStatus.STOPPED

        self._connection_manager = ConnectionManager(
            loop, self.received_message, False
        )
        self._sender_task: asyncio.Task = None

        self._tracker = MessageTracker()
        self.pl31_message_decoder = PowerLink31MessageDecoder()
        self.b0_decoder = B0MessageDecoder()
        self.std_decoder = STDMessageDecoder()
        self._message_queue = MessageQueue()

    def get_profile(self, name: ConnectionName) -> ConnectionProfile | None:
        """Get conneciton profile."""
        for profile in self.connection_profiles:
            if profile.name == name:
                return profile

    async def start(self):
        """Start message coordinator."""

        for connection in self.connection_profiles:
            self._connection_manager.add_connection(connection)

        # Start connection manager
        await self._connection_manager.start()

        self.status = MessageCoordinatorStatus.RUNNING
        _LOGGER.info("Message Coordinator Started")

    async def stop(self):
        """Stop message coordinator."""
        _LOGGER.debug("Stopping Message Coordinator")
        self.status = MessageCoordinatorStatus.CLOSING

        await self._connection_manager.stop()
        self.status = MessageCoordinatorStatus.STOPPED
        _LOGGER.info("Message Coordinator Stopped")

    def received_message(
        self,
        source: ConnectionName,
        client_id: str,
        destination: ConnectionName,
        data: bytes | str,
    ):
        """Handle received message"""
        log_message("\x1b[1;34mMessage ->\x1b[0m %s", data.hex(" "), level=3)
        try:
            if data[1:2].hex() == "b0":
                message = self.b0_decoder.decode_b0_message(data)
            else:
                message = self.std_decoder.decode_standard_message(data)

            if data[2:3].hex() == "02":
                # This is an ACK
                log_message(
                            "\x1b[1;32mACK -> \x1b[1;36mDECODED %s:\x1b[0m %s",
                            source,
                            message.command,
                            message,
                            level=4,
                        )
            else:
                if (
                    isinstance(message, B0Response)
                    and message.type == MessageType.PAGED_RESPONSE.name
                ):
                    log_message("Paged response", level=3)
                    log_message(
                        "\x1b[1;32mDECODED %s:\x1b[0m %s\n",
                        message.command,
                        message,
                        level=2,
                    )
                elif isinstance(message, B0Response) and message.params:
                    log_message(
                        "\x1b[1;32mDECODED %s %s:\x1b[0m %s\n",
                        message.command,
                        message.params,
                        message,
                        level=1,
                    )
                else:
                    log_message(
                        "\x1b[1;32mDECODED %s:\x1b[0m %s\n",
                        message.command,
                        message,
                        level=1,
                    )


        except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.error("\x1b[1;32mFAILED DECODING:\x1b[0m Error is %s", ex)
                _LOGGER.error(traceback.format_exc())

    