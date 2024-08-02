"""Reference lookups."""

import collections
from enum import IntEnum

ZONE_TYPES = [
    "Non-Alarm",
    "Emergency",
    "Flood",
    "Gas",
    "Delay 1",
    "Delay 2",
    "Interior-Follow",
    "Perimeter",
    "Perimeter-Follow",
    "24 Hours Silent",
    "24 Hours Audible",
    "Fire",
    "Interior",
    "Home Delay",
    "Temperature",
    "Outdoor",
    "16",
]


class SensorType(IntEnum):
    """Sensor types enum."""

    IGNORED = -2
    UNKNOWN = -1
    MOTION = 0
    MAGNET = 1
    CAMERA = 2
    WIRED = 3
    SMOKE = 4
    FLOOD = 5
    GAS = 6
    VIBRATION = 7
    SHOCK = 8
    TEMPERATURE = 9
    SOUND = 10


ZoneSensorType = collections.namedtuple("ZoneSensorType", "name func")
SENSOR_TYPES = {
    0x01: ZoneSensorType("Next PG2", SensorType.MOTION),
    0x03: ZoneSensorType("Clip PG2", SensorType.MOTION),
    0x04: ZoneSensorType("Next CAM PG2", SensorType.CAMERA),
    0x05: ZoneSensorType("GB-502 PG2", SensorType.SOUND),
    0x06: ZoneSensorType("TOWER-32AM PG2", SensorType.MOTION),
    0x07: ZoneSensorType("TOWER-32AMK9", SensorType.MOTION),
    0x0A: ZoneSensorType("TOWER CAM PG2", SensorType.CAMERA),
    0x0C: ZoneSensorType("MP-802 PG2", SensorType.MOTION),
    0x0F: ZoneSensorType("MP-902 PG2", SensorType.MOTION),
    0x15: ZoneSensorType("SMD-426 PG2", SensorType.SMOKE),
    0x16: ZoneSensorType("SMD-429 PG2", SensorType.SMOKE),
    0x18: ZoneSensorType("GSD-442 PG2", SensorType.SMOKE),
    0x19: ZoneSensorType("FLD-550 PG2", SensorType.FLOOD),
    0x1A: ZoneSensorType("TMD-560 PG2", SensorType.TEMPERATURE),
    0x1E: ZoneSensorType("SMD-429 PG2", SensorType.SMOKE),
    0x29: ZoneSensorType("MC-302V PG2", SensorType.MAGNET),
    0x2A: ZoneSensorType("MC-302 PG2", SensorType.MAGNET),
    0x2C: ZoneSensorType("MC-303V PG2", SensorType.MAGNET),
    0x2D: ZoneSensorType("MC-302V PG2", SensorType.MAGNET),
    0x35: ZoneSensorType("SD-304 PG2", SensorType.SHOCK),
    0xFE: ZoneSensorType("Wired", SensorType.WIRED),
}

SYSTEM_STATUS = [
    "Disarmed",
    "ExitDelay_ArmHome",
    "ExitDelay_ArmAway",
    "EntryDelay",
    "Stay",
    "Armed",
    "UserTest",
    "Downloading",
    "Programming",
    "Installer",
    "Home Bypass",
    "Away Bypass",
    "Ready",
    "NotReady",
    "??",
    "??",
    "Disarm",
    "ExitDelay",
    "ExitDelay",
    "EntryDelay",
    "StayInstant",
    "ArmedInstant",
    "??",
    "??",
    "??",
    "??",
    "??",
    "??",
    "??",
    "??",
    "??",
    "??",
]
