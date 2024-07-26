"""Data decoders for B0 35 messages."""

from enum import IntEnum, StrEnum
from textwrap import wrap
from ..helpers import b2i
from ..refs import ZONE_TYPES


class Command35Settings(StrEnum):
    """Command 35 settings."""

    # TODO: Convert to int value and reorder!!

    COMMS_CS_REC1_ACCT = "00 00"
    COMMS_CS_REC2_ACCT = "01 00"
    PANEL_SERIAL_NO = "02 00"
    COMMS_CS_REC1_IP = "03 00"
    COMMS_CS_REC1_PORT = "04 00"
    COMMS_CS_REC2_IP = "05 00"
    COMMS_CS_REC2_PORT = "06 00"
    CAPABILITIES = (
        "07 00"  # I think!  Mapping to pmPanelConfig_t looks to match some of it.
    )
    USER_CODES = "08 00"
    ZONE_NAMES = "0d 00"
    DOWNLOAD_CODE = "0f 00"
    POWERLINK_SW_VERSION = "15 01"
    EMAIL_REPORTED_EVENTS = "18 01"  # alarm, alert, trouble, open/close - 4 bytes, 1 for each of 4 email addresses
    SMS_REPORTED_EVENTS = (
        "19 01"  # alarm, alert, trouble, open/close - 4 bytes, 1 for each of 4 tel nos
    )
    MMS_REPORTED_EVENTS = (
        "1a 01"  # alarm, alert, trouble, open/close - 4 bytes, 1 for each of 4 tel nos.
    )
    PANEL_EPROM_VERSION = "24 00"  # ae 08 = 8.174
    TYPE_OFFSETS = "27 00"  # no idea what this means!
    CAPABILITIES2 = "28 00"
    UNKNOWN_SOFTWARE_VERSION = "2b 00"  # JS700421 v1.0.02
    PANEL_DEFAULT_VERSION = "2c 00"
    PANEL_SOFTWARE_VERSION = "2d 00"
    PARTITIONS_ENABLED = "30 00"
    ASSIGNED_ZONE_TYPES = "31 00"
    ASSIGNED_ZONE_NAMES = "32 00"
    UNKNOWN_SW_VERSION = "32 01"
    SOMETHING_ZONES = "33 00"  # Not sure what this is as all 0x00's but 64 bytes
    MAP_VALUE = "34 00"  # Not sure what this is but returns MAP08
    MAP_VALUE_2 = "35 00"  # Not sure what this is but returns MAP08
    SOMETHING_ZONES_2 = "36 00"  # Not sure what this is as all 0x01's but 64 bytes
    SOMETHING_32_OF = "37 00"  # Not sure what this is as all 0x01's but 32 bytes - keypads/tags?  I have none.
    SOMETHING_32_OF_2 = (
        "38 00"  # Not sure as all 0x01's but 32 bytes - keypads/tags?  I have none.
    )
    SOMETHING_8_OF = "39 00"  # Not sure as all 0x01's but 8 bytes - sirens? But I have a wireless one.
    PANEL_HARDWARE_VERSION = "3c 00"
    PANEL_RSU_VERSION = "3d 00"
    PANEL_BOOT_VERSION = "3e 00"
    CUSTOM_ZONE_NAMES = "42 00"
    ZONE_NAMES2 = "45 00"
    CUSTOM_ZONE_NAMES2 = "46 00"
    H24_TIME_FORMAT = "47 00"
    US_DATE_FORMAT = "48 00"
    PARTITIONS = "4e 00"  # THINK- NEEDS CHECKING SHOWS 03
    TROUBLES = "50 01"  # Seems to be trouble/alert texts for panel
    INSTALLER_CODE = "54 00"
    DHCP_IP = "54 01"
    MASTER_CODE = "55 00"  # Value is 60 52
    GUARD_CODE = "56 00"
    EXIT_DELAY = "58 00"
    BYPASS_ARM = "5b 00"
    KIDS_COME_HOME = "5b 01"
    DURESS_CODE = "61 00"
    ENABLE_API = "70 01"
    PANEL_SERIAL = "71 01"
    HOME_AUTOMATION_SERVICE = "73 01"
    ENABLE_SSH = "74 01"
    MAYBE_MAX_USER_CODES = "7b 01"
    COMMS_GPRS_APN = "80 00"
    COMMS_GPRS_USER = "81 00"
    COMMS_GPRS_PWD = "82 00"
    SSL_FOR_IPMP = "85 01"
    LOG_EMAIL_SEND_NOW = "87 01"
    UNKNOWN_EMAIL = "89 01"  # msp5.2cpu.visonic@gmail.com
    UNKNOWN_PWD = "8a 01"  # I think! Wer98Ce651dsa093
    COMMS_CS_REC1_TELNO = "8c 00"
    COMMS_CS_REC2_TELNO = "8d 00"
    DNS_NAME = "8d 01"
    COMMS_CS_REC12_SMS = "8e 00"
    ABORT_TIME = "8e 01"
    ENTRY_DELAY = "8f 01"
    DO_NOT_USE = "9d 01"  # Alarm goes mad sending 255 pages and then repeats! Drops off and needs repower to reconnect.
    EMAIL_ADDRESSES = "a4 00"
    PHONE_NUMBERS = "a5 00"
    VIEW_ON_DEMAND = "a6 00"
    VIEW_ON_DEMAND_TIME_WINDOW = "a7 00"
    LOG_FTP_SITE = "a8 01"  # ftp://Pm360logger.visonic.com:990
    LOG_FTP_UID = "a9 01"  # plink360
    LOG_FTP_PWD = "aa 01"  # plink360visonic
    DHCP_MODE = "ae 00"
    POWERLINK_IP = "af 00"
    POWERLINK_SUBNET = "b0 00"
    POWERLINK_GATEWAY = "b1 00"
    USER_PARTITION_ACCESS = (
        "e2 00"  # user is 1 byte - partition id is bit setting ie 7 = 0111
    )
    USER_CODES2 = "e5 00"
    PANEL_LANGUAGE = "e8 00"
    ACCEPTED_CHARS_UPPER = "e9 00"
    ACCEPTED_CHARS_LOWER = "ea 00"
    INVESTIGATE_MORE = "eb 00"  # looks zone related but not sure


class MessageB035DataDecoder:
    """Decode B0 35 message data."""

    def m35_07_00_decoder(self, data: bytes) -> dict:
        """Decode CAPABILITIES message.

        Data is in 2 bytes little endian ints
        Index of value matches IndexName
        """

        class B03507IndexName(IntEnum):
            """Index name."""

            REPEATERS = 0
            X10 = 1
            SIRENS = 2
            ZONES = 3
            KEYPADS = 4
            KEYFOBS = 5
            USERCODES = 6
            CAMERASA = 7
            UNK8 = 8
            POWERLINK = 9
            TAGS = 10
            CAMERASB = 11
            PANEL = 12
            UNK13 = 13
            EVENTS = 14
            PARTITIONS = 15
            UNK16 = 16
            UNK17 = 17
            UKN18 = 18
            UNK19 = 19

        capabilities = {}
        for i in range(0, len(data) - 1, 2):
            capabilities[B03507IndexName(int(i / 2)).name] = b2i(
                data[i : i + 2], big_endian=False
            )
        return capabilities

    def m35_08_00_decoder(self, data: bytes) -> dict:
        """Decode USER CODES message.

        Data is in 2 byte undecoded string
        """
        # convert data into hex and then split every 4 digits
        data = data.hex()
        user_codes = {}
        for idx, i in enumerate(range(0, len(data) - 1, 4)):
            code = data[i : i + 4]
            if code != "0000":
                user_codes.update({idx + 1: code})
        return user_codes

    def m35_31_00_decoder(self, data: bytes) -> dict:
        """Decode ASSIGNED_ZONE_TYPE message.

        Data is in 1 byte ints and shows all 64 zones
        """
        zone_types = []
        for i in range(0, len(data) - 1):
            try:
                # lookup zone name
                zone_types.append(ZONE_TYPES[b2i(data[i : i + 1], big_endian=False)])
            except IndexError:
                zone_types.append("UNKNOWN")

        return zone_types

    def m35_32_00_decoder(self, data: bytes) -> dict:
        """Decode ASSIGNED_ZONE_NAMES message.

        Data is in 1 byte ints and shows all 64 zones
        """
        zone_names = []
        for i in range(0, len(data) - 1):
            try:
                # lookup zone name
                zone_names.append(b2i(data[i : i + 1], big_endian=False))
            except IndexError:
                zone_names.append("UNKNOWN")

        return zone_names

    def m35_45_00_decoder(self, data: bytes) -> int:
        """Decode zone names lookup list.

        Multipage response with each entry seperated by \n
        """
        names = [
            name.rstrip(" ") for name in data.decode("ascii").split("\n") if name != ""
        ]
        return names

    def m35_46_00_decoder(self, data: bytes) -> int:
        """Decode zone names lookup list.

        Multipage response with each entry seperated by \n
        """
        return self.m35_45_00_decoder(data)

    def m35_54_01_decoder(self, data: bytes) -> int:
        """Decode dhcp info

        string just needs seperating into 3 lots of 4 x 3 chars
        """
        items = wrap(data.hex(), 12)

        ip = ".".join(wrap(items[0], 3))
        subnet = ".".join(wrap(items[1], 3))
        gateway = ".".join(wrap(items[2], 3))
        return {"IP": ip, "Subnet": subnet, "Gateway": gateway}
