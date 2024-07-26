"""Helper functins"""

import datetime as dt
from datetime import datetime
from functools import reduce
from itertools import batched
import logging
from enum import Enum, StrEnum
import socket
from typing import Any

from .config import MESSAGE_LOG_LEVEL
from .const import TEXT_UNKNOWN


_LOGGER = logging.getLogger(__name__)


def log_message(message: str, *args, level: int = 5):
    if MESSAGE_LOG_LEVEL >= level:
        _LOGGER.info(message, *args)


def slugify(value: str):
    """Slugify."""
    return value.replace(" ", "_")


def get_lookup_value(lookup_enum: Enum | StrEnum, value: Any) -> str | int:
    """Get key from value for Enum."""
    try:
        return lookup_enum(value).name
    except ValueError:
        if isinstance(lookup_enum, Enum):
            return None
        return TEXT_UNKNOWN


def b2i(byte: bytes, big_endian: bool = True) -> int:
    """Convert hex to byte."""
    if big_endian:
        return int.from_bytes(byte, "big")
    return int.from_bytes(byte, "little")


def i2b(number: int, size: int = 1) -> bytes:
    """Convert int to byte"""
    return number.to_bytes(size, "big")


def i2h(number: int, size: int = 1) -> str:
    """Convert int to hex"""
    return i2b(number, size).hex(" ")


def bytes2bits_string(data: bytes, endian: str = "little") -> str:
    """Convert bytes to string of bit representation."""
    length = len(data)
    fmt_str = f"0{length*8}b"
    b = int.from_bytes(data, endian)
    return format(b, fmt_str)


def decode_hex_timestamp(data: bytes) -> datetime:
    """Convert hex timestamp to datetime."""
    ts = data[::-1]
    timestamp = reduce(lambda s, x: s * 256 + x, bytearray(ts))
    return datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)


def decode_hex_datetime(data: bytearray) -> datetime:
    """Convert hex to datetime."""
    secs = b2i(data[0])
    mins = b2i(data[1])
    hour = b2i(data[2])
    day = b2i(data[3])
    month = b2i(data[4])
    year = b2i(data[5]) + 2000

    return datetime.strptime(
        f"{year}-{month}-{day}T{hour}:{mins}:{secs}", "%Y-%m-%dT%H:%M:%S"
    )


def chunk_array(data, size) -> list:
    """Split array into chunk of size."""
    return list(batched(data, size))


def chunk_bytearray(data: bytearray, size: int) -> list[bytes]:
    """Split bytearray into sized chunks."""
    return [data[i : i + size] for i in range(0, len(data), size)]


def chunk_hex_string(data: str, size: int) -> list[str]:
    """Split hex data into array of chunks."""
    data = bytearray.fromhex(data)
    chunked = chunk_bytearray(data, size)
    return [chunk.hex(" ") for chunk in chunked]


def chunk_string(data: str, size: int, remove_space_padding: bool = False) -> list[str]:
    """Split a string into array of chunks"""
    if remove_space_padding:
        return [data[i : i + size].rstrip(" ") for i in range(0, len(data), size)]
    return [data[i : i + size] for i in range(0, len(data), size)]


def get_ip():
    """Get host IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except Exception:  # pylint: disable=broad-exception-caught
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def calculate_message_checksum(msg: bytearray) -> bytes:
    """Calculate CRC Checksum"""
    checksum = 0
    for char in msg[0 : len(msg)]:
        checksum += char
    checksum = 0xFF - (checksum % 0xFF)
    if checksum == 0xFF:
        checksum = 0x00
    return checksum.to_bytes(1, "big")
