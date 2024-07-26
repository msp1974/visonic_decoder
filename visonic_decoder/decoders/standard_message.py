"""Decode stanard message."""

from dataclasses import dataclass
from enum import StrEnum

from ..helpers import calculate_message_checksum, get_lookup_value


class StandardCommand(StrEnum):
    """Standard message command."""

    ACK = "02"
    HELLO = "06"
    ACCESS_DENIED = "08"
    EPROM_RW_MODE = "09"
    EXIT_RW_MODE = "0f"
    ARM_ALARM = "a1"
    REQ_STATUS = "a2"
    STATUS_UPDATE = "a5"
    ZONE_TYPE = "a6"
    SET_DATETIME = "ab"
    EPROM_INFO = "3c"
    WRITE_CONFIG = "3d"
    READ_CONFIG = "3e"
    CONFIG_VALUE = "3f"


@dataclass
class STDMessage:
    """Class for standard message."""

    command: int
    command_str: str
    data: bytes
    checksum: bytes
    verified: bool


class STDMessageDecoder:
    """Standard message decoder."""

    def decode_standard_message(self, msg: bytes) -> STDMessage:
        """Get standard message."""
        command = msg[1:2].hex()
        command_str = get_lookup_value(StandardCommand, command)
        data = msg[2:-2]
        checksum = msg[-2:-1].hex()
        verified = (
            True if checksum == calculate_message_checksum(msg[1:-2]).hex() else False
        )

        # decode data if known structure
        if hasattr(self, f"handle_std_{command}_message"):
            data = getattr(self, f"handle_std_{command}_message")(data)
        else:
            data = data.hex(" ")

        return STDMessage(
            command=command,
            command_str=command_str,
            data=data,
            checksum=checksum,
            verified=verified,
        )
