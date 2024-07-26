"""Initiates MITM server."""

import asyncio
import logging

from .connections.manager import ConnectionProfile, ConnectionType

from .const import INJECTOR_PORT, ConnectionName
from .manager import (
    MessageCoordinator,
    MessageCoordinatorStatus,
)


_LOGGER = logging.getLogger(__name__)


class Runner:
    """Runner manager."""

    def __init__(self, evloop):
        self.loop = evloop
        self.mm: MessageCoordinator = None

    async def run(self):
        """Run servers."""
        connections = [
            ConnectionProfile(
                name=ConnectionName.DECODER,
                connection_type=ConnectionType.CLIENT,
                host="127.0.0.1",
                port=INJECTOR_PORT,
            ),
        ]

        self.mm = MessageCoordinator(self.loop, connections)
        await self.mm.start()

        # Give it time to start
        await asyncio.sleep(5)

        while self.mm.status != MessageCoordinatorStatus.STOPPED:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop"""
        await self.mm.stop()
