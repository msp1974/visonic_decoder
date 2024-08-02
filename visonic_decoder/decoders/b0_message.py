"""Decode B0 message."""

from dataclasses import dataclass
from enum import StrEnum
import logging
from textwrap import wrap

from ..refs import SYSTEM_STATUS

from ..const import (
    EVENTS,
    DataType,
    DataTypes,
    IndexName,
    MessageType,
    ZoneBrightness,
    ZoneStatus,
)
from .b0_35_command import Command35Settings, MessageB035DataDecoder
from .b0_42_command import MessageB042DataDecoder

from ..helpers import (
    b2i,
    calculate_message_checksum,
    chunk_bytearray,
    decode_hex_datetime,
    decode_hex_timestamp,
    get_lookup_value,
    log_message,
    slugify,
)


_LOGGER = logging.getLogger(__name__)

FINAL_PAGE = 255


class B0Command(StrEnum):
    """B0 Message command."""

    ZONE01 = "01"  # Investigate more
    ZONE02 = "02"  # Investigate more
    ZONE04 = "04"  # Investogate more
    ZONE05 = "05"  # Investigate more
    INVALID_COMMAND = "06"
    ZONE07 = "07"  # Investigate more
    # 08 - 0e are some sort of zone / device related but return all 0.
    UNKNOWN0F = "0f"  # Investigate more
    # 10 is invalid command
    # 11 - 16 all return 64 bits of 0 - Zone related?
    ZONES11 = "11"
    ZONES12 = "12"
    ZONES13 = "13"
    ZONES14 = "14"
    ZONES15 = "15"
    ZONES16 = "16"
    REQUEST_LIST = "17"  # with params, alarm sends list of responses.  Without params, sends list of 59, 0f, 11-16, 51-58, 5b, 62, 64, 66, 69, 6d, 6e, 71, 75-77, 7a-7c.
    SENSOR_DETECTION = (
        "18"  # shows for contact and moition - prob others bit = 1 if active, 0 if not
    )
    BYPASSES = "19"
    ENROLLED = "1d"  # Seems to have a 1 bit for each enrolled device
    DEVICE_TYPES = "1f"
    ASSIGNED_NAMES = "21"
    SYSTEM_CAPABILITIES = "22"
    PANEL_STATUS = "24"
    CAMERA_SOMETING = "27"
    STANDARD_EVENT_LOG = "2a"  # Sends 58 pages of data! With 1000, 10 byte entries
    # 2a does not decode - causes error - need to fix!
    UNKNOWN2B = "2b"  # Investigate more
    # 2c is invalid command
    ASSIGNED_ZONE_TYPES = "2d"
    # 30 - 34 - some sort of zone data in 64 bits - all 0
    SETTINGS = "35"  # Needs a parameter for the setting - see b0_35_command.py
    LEGACY_EVENT_LOG = "36"  # Decode fails - investigate more - possibly event log
    SOME_EVENT37 = "37"  # Seems to be 1 event - last/alarm/trouble??  0c 00 93 9e 7d 66 - as of 8/7/24 - still same - shows 27/06/2024 17:17:07
    # 39 - invalid
    ZONE3A = "3a"  # Some zone info in bits
    # 3b, 3c are invalid
    ZONE_TEMPS = "3d"
    # 3e, 3f - invalid
    ZONE40 = "40"  # Some zone info - has data for each zone in use 04
    # 41 gets no response
    SETTINGS2 = "42"  # Need a parameter for the setting - see b0_42_command.py
    ZONE43 = "43"  # Some zone info in 64 bits - all 0
    # 44 - 47 invalid
    ZONE49 = "49"  # SOme zone based info in 64 bytes all 00
    # 4a invalid
    ZONE_LAST_EVENT = "4b"
    # 4c, 4d invalid
    ZONE4E = "4e"  # some zone info in 64 bits - all 0
    ZONE4F = "4f"  # some zone info in 64 bits - all 0
    ZONE50 = "50"  # some zone info in 2 byte words - all 0
    ASK_ME = "51"
    DEVICE_COUNTS = "52"
    CAMERA_SOMETHING = "53"
    GSM_STATUS = "59"
    PANEL_SOFTWARE_VERSION = "64"
    PANEL_EPROM_AND_SW_VERSION = "69"
    KEEP_ALIVE = "6a"
    SOME_LOG = "75"
    ZONE_BRIGHTNESS = "77"


@dataclass
class B0DataChunk:
    """Class to hold a data chunk."""

    data_type: int
    index: int
    length: int
    data: bytearray | list[bytearray]
    hex: str | list[str]


@dataclass
class B042DataChunk(B0DataChunk):
    """B0 command 42 data chunk."""

    max_entries: int
    entries: int
    start_entry: int
    chunk_size: int


@dataclass
class B0StructuredResponseMessage:
    """Class to hold structured/raw decoded b0 response message."""

    message_start_marker: str
    b0_message: bool
    message_type: int
    command: str
    length_all_data: int
    has_params: bool
    params: str
    page: int
    data: list[B0DataChunk | B042DataChunk]
    message_counter: int
    end_data_marker: str
    checksum: str
    message_end_marker: str
    message: str

    def __repr__(self) -> str:
        return (
            f"B0StructuredResponseMessage(message_start_marker={self.message_start_marker}, "
            f"b0_message={self.b0_message}, message_type={self.message_type}, command={self.command}, "
            f"length_all_data={self.length_all_data}, has_params={self.has_params}, params={self.params}, "
            f"page={self.page}, data={self.data}, message_counter={self.message_counter},"
            f"end_data_marker={self.end_data_marker}, checksum={self.checksum}, "
            f"message_end_marker={self.message_end_marker}, "
            f"message={self.message.hex(' ') if isinstance(self.message, bytes) else self.message})"
        )


@dataclass
class B0StructuredRequestMessage:
    """Class to hold structured/raw decoded b0 request message."""

    message_start_marker: str
    b0_message: bool
    message_type: int
    command: str
    length_all_data: int
    has_params: bool
    param_size: int
    data_type: int
    start_of_data_pos: int
    data_length: int
    data: bytearray
    hex: str
    end_data_marker: str
    checksum: str
    message_end_marker: str
    message: str

    def __repr__(self) -> str:
        return (
            f"B0StructuredRequestMessage(message_start_marker={self.message_start_marker}, "
            f"b0_message={self.b0_message}, message_type={self.message_type}, command={self.command}, "
            f"length_all_data={self.length_all_data}, has_params={self.has_params}, param_size={self.param_size}, "
            f"data_type={self.data_type}, start_of_data_pos={self.start_of_data_pos}, data_length={self.data_length}, "
            f"data={self.data}, hex={self.hex}, end_data_marker={self.end_data_marker}, checksum={self.checksum},"
            f"message_end_marker={self.message_end_marker},"
            f"message={self.message.hex(' ') if isinstance(self.message, bytes) else self.message})"
        )


@dataclass
class B0Request:
    """B0 Request."""

    type: str
    command: int
    cmd_name: str
    length: int
    data: bytes
    checksum: bytes
    verified: bool


@dataclass
class B0DecodedData:
    """B0 decoded data"""

    data: list | dict


@dataclass
class B0GenDecodedData(B0DecodedData):
    """B0 Gen decoded data"""

    length: int


@dataclass
class B0Cmd35DecodedData(B0DecodedData):
    """B0 Cmd35 decoded data"""

    length: int
    config: str
    config_str: str
    data_type: str


@dataclass
class B0Cmd42DecodedData(B0Cmd35DecodedData):
    """B0 Cmd42 decoded data"""


@dataclass
class B0Response:
    """B0 Response."""

    type: str
    command: int
    cmd_name: str
    params: str
    page: int
    length: int
    data: B0DecodedData | B0GenDecodedData | B0Cmd35DecodedData
    checksum: bytes
    verified: bool


class PagedMessageManager:
    """Tracking a paged message."""

    def __init__(self):
        """Init."""

        self.command: str | None = None
        self.last_page: int = 0
        self.pages: dict[str, B0StructuredResponseMessage] = {}

    def has_active_paged_response(self, command: str) -> bool:
        """Return if page tracker exists for command."""
        if self.pages:
            # b0 ff doesn't send a page ff
            if self.pages.get(
                f"{command}_1"
            ):  # and not self.pages.get(f"{command}_ff"):
                return True
        return False

    def clear_command_pages(self, command: str):
        """Clear any stored pages for command."""
        for page_id, _ in self.pages.items():
            if page_id.split("_")[0] == command:
                self.pages.pop(page_id)

    def add_page(
        self, command: str, page_no: int, message: B0StructuredResponseMessage
    ):
        """Add to paged repsonse tracker"""
        if page_no == 1:
            # Remove any previous pages for this command
            self.reset()

        page_id = f"{command}_{page_no}"
        self.pages[page_id] = message
        log_message(
            "Adding page %s for command %s to paged tracker", page_no, command, level=4
        )

    def get_highest_page_for_command(self, command) -> int:
        """Get highest page number of stored pages."""
        page_ids = [
            page_id.split("_")[1]
            for page_id in self.pages
            if page_id.split("_")[0] == command
        ]
        if not page_ids:
            return 0
        page_ids.sort()
        return int(page_ids[:-1])

    def get_pages(self, command: str) -> dict[int, B0StructuredResponseMessage]:
        """Get amalgamated message."""
        response: dict[str, bytes] = {}
        for page_id, message in self.pages.items():
            if page_id.split("_")[0] == command:
                response[page_id.split("_")[1]] = message

        return response

    def reset(self):
        """Reset paged message tracker to empty."""
        self.pages = {}


class B0MessageDecoder:
    """Decode a B0 message."""

    def __init__(self):
        """Init."""
        self.paged_message_manager = PagedMessageManager()

    def _get_data_type(self, data_type: int) -> str:
        """Get type of data."""
        try:
            return DataType(data_type).name
        except ValueError:
            return f"UNKNOWN-{data_type}"

    def _data_type_decoder(
        self, data_type: int, data: bytearray, string_size: int = 16
    ) -> int | str | bytearray:
        if data_type == DataType.ZERO_PADDED_STRING:  # \x00 padded string
            return data.decode("ascii", errors="ignore").rstrip("\x00")
        elif data_type == DataType.DIRECT_MAP_STRING:  # Direct map to string
            return data.hex()
        elif data_type == DataType.FF_PADDED_STRING:
            return data.hex().replace("ff", "")
        elif data_type == DataType.DOUBLE_LE_INT:  # 2 byte int
            return (
                [b2i(data[i : i + 2], False) for i in range(0, len(data), 2)]
                if len(data) > 2
                else b2i(data[0:2], False)
            )
        elif data_type == DataType.INTEGER:  # 1 byte int?
            if isinstance(data, list | bytes):
                return (
                    [data[i] for i in range(0, len(data))]
                    if len(data) > 1
                    else data[0]
                    if data
                    else None
                )
            else:
                return b2i(data, big_endian=False)
        elif data_type == DataType.STRING:
            return data.decode("ascii", errors="ignore")
        elif data_type == DataType.SPACE_PADDED_STRING:  # Space padded string
            return data.decode("ascii", errors="ignore").rstrip(" ")
        elif (
            data_type == DataType.SPACE_PADDED_STRING_LIST
        ):  # Space paddeded string list - seems all 16 chars
            # Cmd 35 0d 00 can include a \x00 instead of \x20 (space)
            # Remove any \x00 also when decoding.
            names = wrap(data.decode("ascii"), string_size)
            if names and len(names) == 1:
                return names[0].replace("\x00", "").rstrip(" ")
            else:
                return [
                    name.replace("\x00", "").rstrip(" ") for name in names if name != ""
                ]
        return data.hex(" ")

    def create_message_from_paged_messages(
        self,
        message: B0StructuredResponseMessage,
        paged_messages: dict[int, B0StructuredResponseMessage],
    ) -> B0StructuredResponseMessage:
        """Create a single message from a dict of paged messages

        Use message (should be he last (page 255) message) as main output message
        and combine data chunks for other messages
        Also increase length counts etc.
        """
        paged_messages.update({message.page: message})
        all_data = self.rebuild_paged_data_chunks(paged_messages)
        message.data = all_data
        return message

    def rebuild_paged_data_chunks(
        self, messages: dict[int, B0StructuredResponseMessage]
    ) -> list[B0DataChunk]:
        """Rebuild chunks from a paged response into a single set of chunkks.

        Handles chunks that are split across pages of same data type and index number

        """
        chunks: list[B0DataChunk] = []

        def have_partial_chunk(chunk: B0DataChunk) -> bool:
            """Check if alreay have a chunk with same index in chunks array"""
            for existing_chunk in chunks:
                if existing_chunk.index == chunk.index:
                    return True
            return False

        def add_chunk_data_to_exisitng_chunk(chunk: B0DataChunk):
            """Add data from one chunk to exisitng one."""
            for idx, existing_chunk in enumerate(chunks):
                if existing_chunk.index == chunk.index:
                    chunks[idx].data.extend(chunk.data)
                    chunks[idx].hex.extend(chunk.hex)
                    chunks[idx].length = chunks[idx].length + chunk.length

        for _, message in messages.items():
            for chunk in message.data:
                if have_partial_chunk(chunk):
                    add_chunk_data_to_exisitng_chunk(chunk)
                else:
                    chunks.append(chunk)
        return chunks

    def validate_b0_message(self, struct_msg: B0StructuredResponseMessage) -> bool:
        """Validate our message

        Check start and end chars
        Check data end char is 0x43
        Validate checksum
        """
        if (
            struct_msg.message_start_marker == "0d"
            and struct_msg.end_data_marker == "43"
            and calculate_message_checksum(
                struct_msg.message[:-1]
            ).hex()  # remove checksum form msg
            == struct_msg.checksum
            and struct_msg.message_end_marker == "0a"
        ):
            return True
        return False

    def decode_b0_message(self, msg: bytes) -> B0Request | B0Response:
        """Get B0 message."""
        # Testing!
        message = self.decode_b0_message_structure(msg)

        log_message("Structured Message: %s", message, level=4)

        verified = self.validate_b0_message(message)

        if message.message_type in (
            MessageType.ADD,
            MessageType.REQUEST,
            MessageType.REMOVE,
        ):
            # data = self.decode_b0_request(msg)
            # Get best data format for reading
            return B0Request(
                type=get_lookup_value(MessageType, message.message_type),
                command=message.command,
                cmd_name=get_lookup_value(B0Command, message.command),
                length=message.data_length,
                data=message.data
                if isinstance(message.data, B0DataChunk)
                else [
                    chunk.hex(" ")
                    for chunk in chunk_bytearray(message.data, message.param_size)
                ]
                if message.has_params
                else message.data.hex(" "),
                checksum=message.checksum,
                verified=verified,
            )

        elif message.message_type == MessageType.PAGED_RESPONSE:
            # Data added to paged amalgamation

            # Fix for b0 1f that does not confirm to normla paging strucutre
            # and send page ff for all pages which cannnot be the page number
            # for a paged response.
            page_no = message.page
            if page_no == 255:
                last_page = self.paged_message_manager.get_highest_page_for_command(
                    message.command
                )
                page_no = last_page + 1

            self.paged_message_manager.add_page(message.command, page_no, message)
            return B0Response(
                type=get_lookup_value(MessageType, message.message_type),
                command=message.command,
                cmd_name=get_lookup_value(B0Command, message.command),
                params=message.params,
                length=message.length_all_data,
                page=message.page,
                data=message.data,
                checksum=message.checksum,
                verified=verified,
            )

        else:
            if self.paged_message_manager.has_active_paged_response(message.command):
                # self.paged_message_manager.add_page(
                #    message.command, message.page, message
                # )
                paged_messages = self.paged_message_manager.get_pages(message.command)
                message = self.create_message_from_paged_messages(
                    message, paged_messages
                )
                self.paged_message_manager.reset()

                # _LOGGER.debug("UNPAGED: %s", message)

            # decode data if known structure

            if hasattr(self, f"b0_{message.command}_data_decoder"):
                log_message("Using %s", f"b0_{message.command}_data_decoder", level=3)
                decoded_data = getattr(self, f"b0_{message.command}_data_decoder")(
                    message
                )
            else:
                log_message("Using generic data decoder", level=3)
                decoded_data = self.b0_gen_data_decoder(message)

            return B0Response(
                type=get_lookup_value(MessageType, message.message_type),
                command=message.command,
                cmd_name=get_lookup_value(B0Command, message.command),
                params=message.params,
                length=message.length_all_data,
                page=message.page,
                data=decoded_data,
                checksum=message.checksum,
                verified=verified,
            )

    def decode_b0_message_structure(
        self, msg: bytes
    ) -> B0StructuredRequestMessage | B0StructuredResponseMessage:
        """Decode a B0 response into its parts

        command 0f does not follow.  Need to acocmodate

        """
        message_start_marker = msg[:1].hex()
        b0_message = msg[1:2].hex() == "b0"
        message_type = b2i(msg[2:3])  # See MessageType
        command = msg[3:4].hex()
        length_all_data = b2i(msg[4:5])

        # End message elements
        message_counter = b2i(msg[-4:-3])
        end_data_marker = msg[-3:-2].hex()
        checksum = msg[-2:-1].hex()
        message_end_marker = msg[-1:].hex()

        # Not sure there are really correct names - need to get names right
        if message_type in [MessageType.ADD, MessageType.REMOVE]:
            # On both of these - called when adding and removing devices - what else?
            # download code is in bytes 5 & 6
            # 0d b0 00 25 10 aa aa 01 ff 08 ff 09 31 34 30 35 30 31 39 07 00 43 03 0a
            # 5 & 6 download code, 12 -> 18 is enrollment id, 19 is zone id (based on 0 being first) to enroll to.
            # 0d b0 04 25 09 aa aa 01 ff 08 03 02 08 00 43 6e 0a
            # bytes 5 & 6 download code, 7 dont know, 9 data type, 10 index, 11 length, 12 zone to unenroll from
            # download_code = msg[6:7]
            # Set bypass zone - 4
            # 0d b0 00 19 0f aa aa 00 ff 01 03 08 08 00 00 00 00 00 00 00 43 7a 0a

            # Remove bypass zone 4
            # 0d b0 04 19 0f aa aa 00 ff 01 03 08 08 00 00 00 00 00 00 00 43 76 0a

            if msg[10:11] == b"\xff":
                # byte 11 is data length
                data_type = b2i(msg[9:10])
                data_length = b2i(msg[11:12])
                start_of_data = 12
                data = bytearray(msg[start_of_data : start_of_data + data_length])
            else:
                # byte 10 is data length
                data_type = b2i(msg[9:10])
                data_length = length_all_data - 4
                start_of_data = 12
                chunk_length = b2i(msg[11:12])
                data = B0DataChunk(
                    data_type=b2i(msg[9:10]),
                    index=b2i(msg[10:11]),
                    length=chunk_length,
                    data=bytearray(msg[start_of_data : start_of_data + chunk_length]),
                    hex=msg[start_of_data : start_of_data + chunk_length].hex(" "),
                )

            return B0StructuredRequestMessage(
                message_start_marker=message_start_marker,
                b0_message=b0_message,
                message_type=message_type,
                command=command,
                length_all_data=length_all_data,
                has_params=False,
                param_size=0,
                data_type=data_type,
                start_of_data_pos=start_of_data,
                data_length=data_length,
                data=data,
                hex=data.hex(" ") if isinstance(data, bytearray) else None,
                end_data_marker=end_data_marker,
                checksum=checksum,
                message_end_marker=message_end_marker,
                message=msg[1:-1],
            )

        # Requests have a slightly different structure
        elif message_type == MessageType.REQUEST:
            # They can be simple requests or requests with parameters.
            # Parameters can be 1 or more in a 2 byte list
            if length_all_data > 1:
                # This is a param request
                has_params = True
                param_size = b2i(msg[5:6])
                data_type = b2i(msg[7:8])
                data_length = b2i(msg[9:10])
                start_of_data = 10
                data = msg[start_of_data : start_of_data + data_length]
            else:
                has_params = False
                param_size = 0
                data_type = -1
                data_length = b2i(msg[4:5])
                start_of_data = 5
                data = msg[start_of_data : start_of_data + data_length]

            return B0StructuredRequestMessage(
                message_start_marker=message_start_marker,
                b0_message=b0_message,
                message_type=message_type,
                command=command,
                length_all_data=length_all_data,
                has_params=has_params,
                param_size=param_size,
                data_type=data_type,
                start_of_data_pos=start_of_data,
                data_length=data_length,
                data=bytearray(data),
                hex=data.hex(" "),
                end_data_marker=end_data_marker,
                checksum=checksum,
                message_end_marker=message_end_marker,
                message=msg[1:-1],
            )

        elif message_type in [
            MessageType.PAGED_RESPONSE,
            MessageType.RESPONSE,
            MessageType.UNKNOWN,
        ]:
            # Response message (message type 2 - paged repsonse, 3 - last page response
            # Maybe only 1 page of response so just a 3 sent

            # Setup variables
            has_params = False
            params = ""

            # message type = 3, this is always ff (last page)
            # message type = 2, this is page number
            page = b2i(msg[5:6])

            # now we need to iterate the rest of the data
            # it is in the form
            # data_type index chunk_length data
            # or if data_type of first chunk is 0, then data_type is in later 2 bytes and data starts 3 bytes later
            # within a chunk, the data is organised in lengths of data type
            # this can repeat within the data

            # first get each chunk
            # each chunk is ff 08 ff 10 [16 bytes]
            # first chunk byte 1 is page no so can be 01, 02 etc
            if b2i(msg[6:7]) == 0:
                i = 9  # Some sort of ref to say the data type in 8 and 9
                # only a single chunk in this case
                data_length = b2i(msg[11:12])
                data = msg[12 : 12 + data_length]
                struct_chunks = [
                    B0DataChunk(
                        data_type=b2i(msg[6:7]),
                        index=255,
                        length=data_length,
                        data=bytearray(data),
                        hex=data.hex(" "),
                    )
                ]

            elif command == "0f":
                # Handle 0f command which does not seem to follow normal
                # message structure.
                data_type = b2i(msg[6:7])
                index = 255
                data_length = b2i(msg[4:5]) - 4
                data_size_bytes = max(1, int(data_type / 8))
                data = chunk_bytearray(msg[8 : 8 + data_length], data_size_bytes)

                struct_chunks = [
                    B0DataChunk(
                        data_type=data_type,
                        index=index,
                        length=data_length,
                        data=data,
                        hex=[d.hex() for d in data],
                    )
                ]

            elif command == "35":
                # Seen in 35 (maybe more)
                # bytes 9 and 10 are the config parameter and therefore
                # We should only have 1 chunk per message
                # our data actually starts at 12
                has_params = True
                params = msg[9:11].hex(" ")

                data_type = b2i(msg[11:12])
                data_length = b2i(msg[8:9]) - 3
                data_size_bytes = max(1, int(data_type / 8))
                data = chunk_bytearray(msg[12 : 12 + data_length], data_size_bytes)
                struct_chunks = [
                    B0DataChunk(
                        data_type=data_type,
                        index=255,
                        length=data_length,
                        data=data,
                        hex=[d.hex() for d in data],
                    )
                ]

            elif command == "42":
                # Seen in 42 messages (maybe more)
                # bytes 9 and 10 are the config parameter and therefore
                # We should only have 1 chunk per message
                # our data actually starts at 11
                # This needs more validation

                has_params = True

                data_length = b2i(msg[8:9]) - 14
                params = msg[9:11].hex(" ")
                max_entries = b2i(msg[11:13], big_endian=False)
                data_chunk_size = int(b2i(msg[13:15], big_endian=False) / 8)
                data_type = b2i(msg[17:18])
                start_entry = b2i(msg[19:21], big_endian=False)

                # Fix for some returns that have a data tyoe of 04 ff.  Assumed 4 (integer) but they
                # are Zero padded strings.  May need to look at that second data type byte for 42s.
                # if data_type == 4 and b2i(msg[18:19]) == 255:
                #    data_type = 10

                entries = b2i(msg[21:23], big_endian=False)
                data_size_bytes = max(1, int(data_type / 8))
                if data_chunk_size == 0:
                    data = []
                else:
                    data = chunk_bytearray(msg[23 : 23 + data_length], data_chunk_size)
                struct_chunks = [
                    B042DataChunk(
                        data_type=data_type,
                        index=255,
                        length=data_length,
                        chunk_size=data_chunk_size,
                        max_entries=max_entries,
                        entries=entries,
                        start_entry=start_entry,
                        data=data,
                        hex=[d.hex() for d in data],
                    )
                ]

            else:
                # start of first chunk - technically page no on
                # first chunk but we will drop first byte of each chunk
                i = 5

                chunks: list[bytearray] = []
                while i <= length_all_data - 1:
                    chunk_data_length = b2i(msg[i + 3 : i + 4])
                    chunk_data = msg[i + 1 : i + 4 + chunk_data_length]
                    chunks.append(chunk_data)
                    i = i + 4 + chunk_data_length

                # _LOGGER.debug("CHUNKS: %s", chunks)

                # Now process each chunk to split into B0DataChunks
                struct_chunks = []
                for chunk in chunks:
                    data_type = b2i(chunk[:1])

                    # data could be in bits but atm only split into bytes.
                    # We will convert to bits later as we know this by our data_type param on the chunk

                    data_size_bytes = max(1, int(data_type / 8))
                    data = chunk_bytearray(chunk[3:], data_size_bytes)

                    struct_chunks.append(
                        B0DataChunk(
                            data_type=b2i(chunk[:1]),
                            index=b2i(chunk[1:2]),
                            length=b2i(chunk[2:3]),
                            data=data,
                            hex=[d.hex(" ") for d in data],
                        )
                    )

            return B0StructuredResponseMessage(
                message_start_marker=message_start_marker,
                b0_message=b0_message,
                message_type=message_type,
                command=command,
                length_all_data=length_all_data,
                has_params=has_params,
                params=params,
                page=page,
                data=struct_chunks,
                message_counter=message_counter,
                end_data_marker=end_data_marker,
                checksum=checksum,
                message_end_marker=message_end_marker,
                message=msg[1:-1],
            )

    def b0_gen_data_decoder(
        self, message: B0StructuredResponseMessage
    ) -> B0GenDecodedData:
        """Process general data."""

        decoded_chunks = []
        for chunk in message.data:
            if isinstance(chunk.data, list):
                hex_data = [d.hex(" ") for d in chunk.data]
            else:
                hex_data = chunk.data.hex(" ")
            decoded_chunks.append(
                {
                    "type": DataTypes(chunk.data_type).name,
                    "idx": chunk.index,
                    "idx_name": f"{IndexName(chunk.index).name}",
                    "len": chunk.length,
                    "data": hex_data,
                }
            )

        return B0GenDecodedData(length=message.length_all_data, data=decoded_chunks)

    def b0_0f_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 0f message"""
        return B0DecodedData(data=message.data[0])

    def b0_22_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 22 messgae - panel capabilities.

        We get 1 chunk of data split into 21 item 2 byte array

        Iterate each value in data, convert to little endian int and lookup
        value name from IndexName
        """
        chunk = message.data[0]
        capabilities = {}

        for idx, data in enumerate(chunk.data):
            try:
                capability_name = IndexName(idx).name
                capabilities[capability_name] = b2i(data, big_endian=False)
            except KeyError:
                capabilities[f"Unknown-{idx}"] = b2i(data, big_endian=False)

        return B0DecodedData(data=capabilities)

    def b0_24_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 24 messgae - event message.

        Strucutred message data is

        1 partition - 06 00 00 00 00 00 00 00 13 2f 12 1c 06 18 14 06 01 00 83 00 00
        3 partitions - 07 00 00 00 00 00 00 00 0c 0a 0e 04 07 18 14 05 03 00 83 00 00 00 03 00 00 00 03 00 00

        8 -> 14 is panel datetime in ss mn hh dd mm yy yy
        15 - don't know
        16 - number of partitions
        17 - system status
        22, 26, 30 - partitions status
        23, 27, 31 - troubles?
        24, 28, 32 - gprs
        rest - dont know

        """
        try:
            chunk = message.data[0]
            # index = get_lookup_value(IndexName, chunk.index)
            dte = decode_hex_datetime(chunk.data[8:15]).strftime("%Y-%m-%d %H:%M:%S")
            partition_count = b2i(chunk.data[16])
            partition_data = chunk_bytearray(chunk.data[17:], 4)

            sys_status = {}
            for idx, partition in enumerate(partition_data):
                state = b2i(partition[0])  # byte 0 is armed status
                sys = partition[1][0]  # byte 1 of each chunk is sys status

                sys_status.update(
                    {
                        idx + 1: {
                            "State": SYSTEM_STATUS[state],
                            "Ready": bool(sys & (0b1 << 0)),
                            "Alarm in Memory": bool(sys & (0b1 << 1)),
                            "Trouble": bool(sys & (0b1 << 2)),
                            "Bypass": bool(sys & (0b1 << 3)),
                            "Last 10 Secs": bool(sys & (0b1 << 4)),
                            "Zone Event": bool(sys & (0b1 << 5)),
                            "Status Changed": bool(sys & (0b1 << 6)),
                            "Alarm Event": bool(sys & (0b1 << 7)),
                        }
                    }
                )
            return B0DecodedData(
                data={
                    "datetime": dte,
                    "partitions": partition_count,
                    "states": sys_status,
                },
            )
        except IndexError:
            return {"Invalid Data"}

    def b0_2a_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 2a standard event log message.

        73 f2 97 66 0c 00 00 32 00 75
        0-3 - datetime
        4 - device type - 0c - panel, 09 - plink, 03 - zones
        5 - if device type is zone, zero based zone id
        6 - 0
        7 - event type
        8 - 0
        9 - some sort of sorting id

        Data should be 1 chunk of array with each element as a log entry
        """
        try:
            events = []
            chunk = message.data[0]

            for event in chunk.data:
                date = decode_hex_timestamp(event[:4])
                device_type = b2i(event[4:5])
                zone_id = b2i(event[5:6])
                event_type = b2i(event[7:8])

                device_name = get_lookup_value(IndexName, device_type)
                if device_type == 3:
                    zone_id = zone_id + 1
                event_name = EVENTS[event_type]

                events.append(
                    {
                        "dt": date.strftime("%Y-%m-%d %H:%M:%S"),
                        "device": device_name,
                        "zone": zone_id,
                        "event": event_name,
                    }
                )

            return B0DecodedData(data=events)
        except IndexError:
            return B0DecodedData(data="Invalid Data")

    def b0_35_data_decoder(
        self, message: B0StructuredResponseMessage
    ) -> B0Cmd35DecodedData:
        """Decode a 35 command response - alarm settings"""
        # Can be single or multi request
        # 02 ff 08 ff 02 8a 00
        # 02 ff 08 ff 08 0f 00 55 00 54 00 06 01 43 f6 0a
        # byte 4 is length of requests

        # Response
        # ff 08 ff 06 8a 00 04 02 00 00 d0

        # Response or Paged response
        # 0d b0 03 35 08 ff 08 ff 03 48 01 04 ee 43 84 0a

        # Check if specific data decoder in decoder35
        try:
            chunk = message.data[0]

            d35 = MessageB035DataDecoder()
            setting = slugify(message.params)
            data = bytes.join(b"", chunk.data)

            func = f"m35_{setting}_decoder"
            if hasattr(d35, func):
                log_message("Using format decoder: %s", func, level=3)
                decoded = getattr(d35, func)(data)
            else:
                # else use generic decoder for data type
                log_message(
                    "Using generic data format decoder for data type: %s",
                    chunk.data_type,
                    level=3,
                )
                if chunk.data_type != 4:
                    decoded = self._data_type_decoder(chunk.data_type, data)
                else:
                    decoded = [
                        self._data_type_decoder(chunk.data_type, d, 30)
                        for d in chunk.data
                    ]

                if decoded:
                    if len(decoded) == 1:
                        decoded = decoded[0]
                else:
                    decoded = None

            try:
                config_str = Command35Settings(message.params).name
            except ValueError:
                config_str = "Unknown"

            return B0Cmd35DecodedData(
                length=chunk.length,
                config=message.params,
                config_str=config_str,
                data_type=self._get_data_type(chunk.data_type),
                data=decoded,
            )
        except IndexError:
            return {"Invalid Data"}

    def b0_36_data_decoder(
        self,
        message: B0StructuredResponseMessage,
    ) -> B0DecodedData:
        """Decode a 36 legacy log message. Same format as 2a"""
        return self.b0_2a_data_decoder(message)

    def b0_3d_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 3d zone temps message.

        Each byte is a zone temp based on temp = -40.5 + (value/2) to give 0.5C increments
        A value of FF means no temp available.
        """
        try:
            chunk = message.data[0]
            index = get_lookup_value(IndexName, chunk.index)
            zone_temps = {}
            for zone, btemp in enumerate(chunk.data):
                if btemp != b"\xff":
                    zone_temps.update({zone + 1: (b2i(btemp) / 2) - 40.5})
            return B0DecodedData(data={index: zone_temps})
        except IndexError:
            return B0DecodedData(data="Invalid Data")

    def b0_42_data_decoder(
        self, message: B0StructuredResponseMessage
    ) -> B0Cmd42DecodedData:
        """Decode a 42 settings/lookup message.

        0d b0 03 42 13 ff 08 ff 0e 0d 00 00 00 f0 00 00 00 0a 00 00 00 00 00 6a 43 2b 0

        Alarm responses are only ever by a single command (but can be paged repsonses if long)
        """

        try:
            chunk = message.data[0]
            d42 = MessageB042DataDecoder()
            setting = slugify(message.params)

            func = f"m42_{setting}_decoder"
            if hasattr(d42, func):
                log_message("Using format decoder: %s", func, level=3)
                decoded = getattr(d42, func)(chunk.data)
            else:
                # else use generic decoder for data type
                log_message(
                    "Using generic data format decoder for data type: %s",
                    chunk.data_type,
                    level=3,
                )
                decoded = [
                    self._data_type_decoder(chunk.data_type, d, chunk.chunk_size)
                    for d in chunk.data
                ]

                if decoded:
                    if len(decoded) == 1:
                        decoded = decoded[0]
                else:
                    decoded = None

            try:
                config_str = Command35Settings(message.params).name
            except ValueError:
                config_str = "Unknown"

            return B0Cmd42DecodedData(
                length=chunk.length,
                config=message.params,
                config_str=config_str,
                data_type=self._get_data_type(chunk.data_type),
                data=decoded,
            )
        except IndexError:
            return {"Invalid Data"}

    def b0_4b_data_decoder(
        self,
        message: B0StructuredResponseMessage,
    ) -> B0DecodedData:
        """Decode a 4b zone last status message.
        b0 02 4b b4 01 28 03 af b8 b7 86 66 02 80 4e 86 66 04 ce 9a 86 66 04 38 c1 86 66 04 ... e9 43 5e 0a
        b0 03 4b 96 ff 28 03 91 41 ec 6d 38 00 41 ec 6d 38 00 41 ec 6d 38 00 41 ec 6d 38 00 ... ea 43 80 0a

        Each 5 byte entry (starting at byte 8) is zone with a 4 bytes datetime (reverse timestamp) followed by a 1 byte code
        Codes are
        00 - Not a zone
        01 - Open
        02 - Closed
        03 - Motion
        04 - CheckedIn?  As in device checked in.

        Can be a paged response but this is rebuilt before being sent here for decoding
        """
        events = {}

        for chunk in message.data:
            for idx, event in enumerate(chunk.data):
                date = decode_hex_timestamp(event[:4])
                code = event[4:5]
                events.update(
                    {
                        idx + 1: {
                            "datetime": date.strftime("%Y-%m-%d %H:%M:%S"),
                            "code": get_lookup_value(ZoneStatus, b2i(code)),
                        }
                    }
                )

        return B0DecodedData(data=events)

    def b0_51_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 51 ASK ME message.
        18 24 4b
        """
        # Only a response message from the Alarm
        try:
            if message.data:
                chunk = message.data[0]
                return B0DecodedData(data=[d.hex(" ") for d in chunk.data])
        except IndexError:
            return B0DecodedData("Invalid Data")

    def b0_52_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 52 Counts message.

        b0 03 52 0b ff 08 ff 06 19 08 00 02 01 01 fa 43 7d
        ['19', '08', '00', '02', '01', '01']
        0 - don't know
        1 - zones
        2 - don't know - keypads?
        3 - keyfobs
        4 - sirens?
        5 - PGMS?
        """
        try:
            chunk = message.data[0]
            data = chunk.data
            return B0DecodedData(
                data={
                    "Unknown": b2i(data[0]),
                    "Sensors": b2i(data[1]),
                    "Keypads": b2i(data[2]),
                    "Keyfobs": b2i(data[3]),
                    "Sirens": b2i(data[4]),
                    "PGMs": b2i(data[5]),
                }
            )
        except IndexError:
            return B0DecodedData(data="Invalid Data")

    def b0_64_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 64 Panel SW Verision message.
        ff 00 ff 13 00 ff 10 4a 53 37 30 33 36 34 36 20 4b 32 30 2e 32 31 34 33
        byte 6 - data length
        bytes [7: -1] - string data
        """
        try:
            chunk = message.data[0]
            return B0DecodedData(data=chunk.data.decode("ascii", errors="ignore"))
        except IndexError:
            return B0DecodedData("Invalid Data")

    def b0_75_data_decoder(
        self,
        message: B0StructuredResponseMessage,
    ) -> B0DecodedData:
        """Decode a 75 unknown log message."""
        events = []

        for chunk in message.data:
            for event in chunk.data:
                date = decode_hex_timestamp(event[:4])
                code = event[4:]
                events.append(
                    {"dt": date.strftime("%Y-%m-%d %H:%M:%S"), "rest": code.hex(" ")}
                )

        return B0DecodedData(data=events)

    def b0_77_data_decoder(self, message: B0StructuredResponseMessage) -> B0DecodedData:
        """Decode a 77 zone lux data chunk.

        Each byte is a zone lux based on 00 = 2 lux, 01 = 7 lux, 02 = 15 lux
        A value of FF means no lux available.

        We should receive 1 chunk with array of 64 values
        """
        try:
            chunk = message.data[0]
            index = get_lookup_value(IndexName, chunk.index)
            zone_brightness = {}
            for zone, bbrightness in enumerate(chunk.data):
                if bbrightness != b"\xff":
                    zone_brightness.update(
                        {zone + 1: get_lookup_value(ZoneBrightness, b2i(bbrightness))}
                    )
            return B0DecodedData(data={index: zone_brightness})
        except IndexError:
            return B0DecodedData(data="Invalid Data")
