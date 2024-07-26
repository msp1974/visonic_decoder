import asyncio
import logging

from visonic.decoders.b0_message import B0MessageDecoder, B0Response

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
_LOGGER = logging.getLogger(__name__)


class CmdLineDecoder:
    """Command line decoder class."""

    async def decode(self, message: str):
        """Decode input."""
        message_decoder = B0MessageDecoder()

        # Convert to byte array
        byte_message = bytearray.fromhex(message)

        # Option to input message without start and end markers - needs at least
        # start marker
        if byte_message[0] != 0x0D:
            byte_message.insert(0, 0x0D)

        try:
            decoded_msg = message_decoder.decode_b0_message(bytes(byte_message))

            print(f"Message Type: {decoded_msg.type}")
            print(f"Command: {decoded_msg.command} ({decoded_msg.cmd_name})")
            if isinstance(decoded_msg, B0Response):
                print(f"Page: {decoded_msg.page}")
            print(f"Length: {decoded_msg.length}")
            print(f"Data: {decoded_msg.data}")
            print("\n\n\n")

        except Exception:
            print("Exception decoding message.  Check format.")

    async def get_input(self):
        """Get command line input."""
        while True:
            # Get message to decode

            print("-------------------------------")
            print("--- Enter message to decode ---")
            print("-------------------------------")
            print()
            print()
            message = input("Enter Message: ")
            print()

            if message != "":
                await self.decode(message)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    decoder = CmdLineDecoder()
    task = loop.create_task(decoder.get_input(), name="ProxyRunner")
    try:
        loop.run_until_complete(task)
        # server = loop.run_until_complete(proxy_server.run())
    except KeyboardInterrupt:
        _LOGGER.info("Keyboard interrupted. Exit.")
        task.cancel()
        # loop.run_until_complete(proxy_server.stop())
        # loop.run_until_complete(proxy_server.terminate())

    _LOGGER.info("Loop is closed")
    loop.close()
