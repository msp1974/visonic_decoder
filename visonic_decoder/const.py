"""Constants."""

from enum import IntEnum, StrEnum


VISONIC_HOST = "52.58.105.181"
MESSAGE_PORT = 5001
INJECTOR_PORT = 5002

KEEPALIVE_TIMER = 30  # Send Keepalive if no messages in 30 seconds
WATHCHDOG_TIMEOUT = 120  # If no received message on connection for 120s, kill it.

TEXT_UNKNOWN = "UNKNOWN"

VIS_ACK = "VIS-ACK"
VIS_BBA = "VIS-BBA"
ADM_CID = "*ADM-CID"
ADM_ACK = "*ACK"


class InjectorCommands(StrEnum):
    """Injector commands."""


class Commands(StrEnum):
    """Available injector commands."""

    SHUTDOWN = "shutdown"
    SHOW = "show"


class MessagePriority(IntEnum):
    """Message priority enum."""

    IMMEDIATE = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ConnectionName(StrEnum):
    """Connection name enum."""

    DECODER = "Decoder"


class MessageType(IntEnum):
    """Message type."""

    ADD = 0
    REQUEST = 1
    PAGED_RESPONSE = 2
    RESPONSE = 3
    REMOVE = 4
    UNKNOWN = 5


class ArmModes(IntEnum):
    """Arm mode command codes."""

    DISARM = 0x00
    EXIT_DELAY_ARM_HOME = 0x01
    EXIT_DELAY_ARM_AWAY = 0x02
    ENTRY_DELAY = 0x03
    ARM_HOME = 0x04
    ARM_AWAY = 0x05
    WALK_TEST = 0x06
    USER_TEST = 0x07
    ARM_INSTANT_HOME = 0x14
    ARM_INSTANT_AWAY = 0x15


class ArmedMode(IntEnum):
    """Armed mode enum."""

    DISARMED = 0x00
    ARMED_HOME = 0x04
    ARMED_AWAY = 0x05
    WALK_TEST = 0x06


class DataType(IntEnum):
    """Command 35 Message data data types."""

    ZERO_PADDED_STRING = 0
    DIRECT_MAP_STRING = 1
    FF_PADDED_STRING = 2
    DOUBLE_LE_INT = 3
    INTEGER = 4
    STRING = 6
    SPACE_PADDED_STRING = 8
    SPACE_PADDED_STRING_LIST = 10


class DataTypes(IntEnum):
    """Data types for B0 message."""

    UNKNOWN = 0
    BITS = 1
    NIBBLE = 4
    BYTES = 8
    WORD16 = 16
    WORD24 = 24
    WORD32 = 32
    WORD40 = 40
    WORD48 = 48
    WORD56 = 56
    WORD64 = 64
    WORD72 = 72
    WORD80 = 80
    WORD88 = 88
    WORD96 = 96
    WORD104 = 104
    WORD112 = 112


class IndexName(IntEnum):
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
    PARTITIONS = 14
    UNK15 = 15
    UNK16 = 16
    EVENTS = 17
    UKN18 = 18
    UNK19 = 19
    UNK20 = 20
    NA = 255


class ZoneStatus(IntEnum):
    """Zone status enum."""

    NA = 0
    OPEN = 1
    CLOSED = 2
    MOTION = 3
    CHECKIN = 4


class ZoneBrightness(IntEnum):
    """Zone brightness enum."""

    DARKNESS = 0
    PARTIAL_LIGHT = 1
    DAYLIGHT = 2


EVENTS = [
    "None",
    # 1
    "Interior Alarm",
    "Perimeter Alarm",
    "Delay Alarm",
    "24h Silent Alarm",
    "24h Audible Alarm",
    "Tamper",
    "Control Panel Tamper",
    "Tamper Alarm",
    "Tamper Alarm",
    "Communication Loss",
    "Panic From Keyfob",
    "Panic From Control Panel",
    "Duress",
    "Confirm Alarm",
    "General Trouble",
    "General Trouble Restore",
    "Interior Restore",
    "Perimeter Restore",
    "Delay Restore",
    "24h Silent Restore",
    # 21
    "24h Audible Restore",
    "Tamper Restore",
    "Control Panel Tamper Restore",
    "Tamper Restore",
    "Tamper Restore",
    "Communication Restore",
    "Cancel Alarm",
    "General Restore",
    "Trouble Restore",
    "Not used",
    "Recent Close",
    "Fire",
    "Fire Restore",
    "Not Active",
    "Emergency",
    "Remove User",
    "Disarm Latchkey",
    "Confirm Alarm Emergency",
    "Supervision (Inactive)",
    "Supervision Restore (Active)",
    "Low Battery",
    "Low Battery Restore",
    "AC Fail",
    "AC Restore",
    "Control Panel Low Battery",
    "Control Panel Low Battery Restore",
    "RF Jamming",
    "RF Jamming Restore",
    "Communications Failure",
    "Communications Restore",
    # 51
    "Telephone Line Failure",
    "Telephone Line Restore",
    "Auto Test",
    "Fuse Failure",
    "Fuse Restore",
    "Keyfob Low Battery",
    "Keyfob Low Battery Restore",
    "Engineer Reset",
    "Battery Disconnect",
    "1-Way Keypad Low Battery",
    "1-Way Keypad Low Battery Restore",
    "1-Way Keypad Inactive",
    "1-Way Keypad Restore Active",
    "Low Battery Ack",
    "Clean Me",
    "Fire Trouble",
    "Low Battery",
    "Battery Restore",
    "AC Fail",
    "AC Restore",
    "Supervision (Inactive)",
    "Supervision Restore (Active)",
    "Gas Alert",
    "Gas Alert Restore",
    "Gas Trouble",
    "Gas Trouble Restore",
    "Flood Alert",
    "Flood Alert Restore",
    "X-10 Trouble",
    "X-10 Trouble Restore",
    # 81
    "Arm Home",
    "Arm Away",
    "Quick Arm Home",
    "Quick Arm Away",
    "Disarm",
    "Fail To Auto-Arm",
    "Enter To Test Mode",
    "Exit From Test Mode",
    "Force Arm",
    "Auto Arm",
    "Instant Arm",
    "Bypass",
    "Fail To Arm",
    "Door Open",
    "Communication Established By Control Panel",
    "System Reset",
    "Installer Programming",
    "Wrong Password",
    "Not Sys Event",
    "Not Sys Event",
    # 101
    "Extreme Hot Alert",
    "Extreme Hot Alert Restore",
    "Freeze Alert",
    "Freeze Alert Restore",
    "Human Cold Alert",
    "Human Cold Alert Restore",
    "Human Hot Alert",
    "Human Hot Alert Restore",
    "Temperature Sensor Trouble",
    "Temperature Sensor Trouble Restore",
    # New values for PowerMaster and models with partitions
    "PIR Mask",
    "PIR Mask Restore",
    "Repeater low battery",
    "Repeater low battery restore",
    "Repeater inactive",
    "Repeater inactive restore",
    "Repeater tamper",
    "Repeater tamper restore",
    "Siren test end",
    "Devices test end",
    # 121
    "One way comm. trouble",
    "One way comm. trouble restore",
    "Sensor outdoor alarm",
    "Sensor outdoor restore",
    "Guard sensor alarmed",
    "Guard sensor alarmed restore",
    "Date time change",
    "System shutdown",
    "System power up",
    "Missed Reminder",
    "Pendant test fail",
    "Basic KP inactive",
    "Basic KP inactive restore",
    "Basic KP tamper",
    "Basic KP tamper Restore",
    "Heat",
    "Heat restore",
    "LE Heat Trouble",
    "CO alarm",
    "CO alarm restore",
    # 141
    "CO trouble",
    "CO trouble restore",
    "Exit Installer",
    "Enter Installer",
    "Self test trouble",
    "Self test restore",
    "Confirm panic event",
    "n/a",
    "Soak test fail",
    "Fire Soak test fail",
    "Gas Soak test fail",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
    "n/a",
]
