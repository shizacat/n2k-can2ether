"""
Yacht Devices RAW TCP, ydwg02

https://www.yachtd.com/downloads/ydwg02.pdf
"""

import datetime

import can
from enum import Enum

from .base import SrvInterfaceBase


class DirectionMsg(str,  Enum):
    # from NMEA 2000 to application
    RECEIVED = "R"
    # from application to NMEA 2000
    TRANSMITTED = "T"


class YachtdRaw(SrvInterfaceBase):
    """
    Interface to Yacht Devices RAW TCP, ydwg02
    """

    name = "yachtd_raw"

    def convert_can_to_srv(self, msg: can.Message) -> bytes:
        """
        Example:
            17:33:21.107 R 19F51323 01 2F 30 70 00 2F 30 70
            17:33:21.108 R 19F51323 02 00
        """
        raw_message = "{tm} {dir} {id} {data}\r\n".format(
            tm=self._get_time(msg),
            dir=DirectionMsg.RECEIVED.value,
            id=f"{msg.arbitration_id:08X}",
            data=" ".join(f"{byte:02X}" for byte in msg.data),
        )

        return raw_message.encode("ascii")

    def _get_time(self, msg: can.Message) -> str:
        """
        Extract and format time from message
        """
        timestamp = datetime.datetime.fromtimestamp(
            msg.timestamp, datetime.UTC)
        return timestamp.strftime("%H:%M:%S.%f")[:-3]
