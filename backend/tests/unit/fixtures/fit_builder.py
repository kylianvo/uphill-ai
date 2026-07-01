"""Builds a minimal, valid FIT (Flexible and Interoperable Data Transfer)
file in-memory for testing FitParser.parse.

We synthesize bytes here rather than checking in a real Garmin .fit export,
because real activity files contain a rider/runner's actual GPS track (start
point, route, home/finish location) -- that's personal location data and has
no business living in a public test fixture.

Only encodes what FitParser.parse actually reads from "record" messages:
timestamp (field 253, uint32), distance (field 5, uint32, scale 100),
heart_rate (field 3, uint8). Field numbers/types/scale are taken directly
from fitparse's bundled Profile (fitparse.profile.MESSAGE_TYPES[20], the
"record" message).

Note: fitparse's date_time processor only converts a timestamp field to a
datetime when the raw value is >= 0x10000000 (see fitparse/processors.py,
process_type_date_time) -- smaller raw values are left as plain ints. Pass
FIT_EPOCH-relative raw values (this module's `raw_timestamp` helper) to get
real datetimes out of FitParser.parse.
"""

import struct

from fitparse.records import Crc

# FIT timestamps are seconds since 1989-12-31T00:00:00Z, not the Unix epoch.
FIT_UTC_REFERENCE = 631065600

_RECORD_GLOBAL_MESG_NUM = 20
_RECORD_FIELDS = [
    (253, 4, 0x86),  # timestamp: uint32
    (5, 4, 0x86),  # distance: uint32, scale 100 (raw / 100 = meters)
    (3, 1, 0x02),  # heart_rate: uint8
]


def raw_timestamp(unix_seconds: int) -> int:
    """Converts a Unix timestamp to the raw uint32 FIT expects for field 253."""
    return unix_seconds - FIT_UTC_REFERENCE


def build_fit_bytes(records: list[tuple[int, float, int]]) -> bytes:
    """records: list of (raw_fit_timestamp, distance_meters, heart_rate) tuples.

    Produces one "record" message per tuple, preceded by a single definition
    message. No "session" message is included -- FitParser.parse's fallback
    path (backfilling total_distance/duration/avg-max heart rate from the
    record stream when no session is present) is what's under test.
    """
    def_msg = struct.pack("<BBBHB", 0x40, 0, 0, _RECORD_GLOBAL_MESG_NUM, len(_RECORD_FIELDS))
    for field_num, size, base_type in _RECORD_FIELDS:
        def_msg += struct.pack("<BBB", field_num, size, base_type)

    data_msgs = b""
    for ts, dist_m, hr in records:
        data_msgs += struct.pack("<B", 0x00)  # data message header, local type 0
        data_msgs += struct.pack("<IIB", ts, int(round(dist_m * 100)), hr)

    body = def_msg + data_msgs
    header = struct.pack("<BBHI4s", 12, 0x10, 2140, len(body), b".FIT")

    crc = Crc()
    crc.update(header)
    crc.update(body)
    trailer = struct.pack("<H", crc.value)

    return header + body + trailer
