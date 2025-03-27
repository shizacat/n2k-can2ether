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
    separator: bytes = b"\r\n"

    def convert_can_to_srv(self, msg: can.Message) -> bytes:
        """
        Example:
            17:33:21.107 R 19F51323 01 2F 30 70 00 2F 30 70<CR><LF>
            17:33:21.108 R 19F51323 02 00<CR><LF>
        """
        raw_message = "{tm} {dir} {id} {data}\r\n".format(
            tm=self._get_time(msg),
            dir=DirectionMsg.RECEIVED.value,
            id=f"{msg.arbitration_id:08X}",
            data=" ".join(f"{byte:02X}" for byte in msg.data),
        )

        return raw_message.encode("ascii")

    def convert_srv_to_can(self, data: bytes) -> can.Message:
        """
        Example:
            19F51323 01 02<CR><LF>
        """
        data = data.decode("ascii").strip()
        arbitration_id, *data = data.split(" ")
        return can.Message(
            arbitration_id=self._arbitration_id_to_int(arbitration_id),
            data=self._data_to_bytes(data),
            is_extended_id=True,
        )

    def event_after_process_srv2can(self, msg: can.Message) -> bytes:
        """
        Event after processing server message to CAN message
        Send message to applicaton

        Example:
            17:33:21.108 T 19F51323 01 02<CR><LF>
        """
        raw_message = "{tm} {dir} {id} {data}\r\n".format(
            tm=self._get_time(msg),
            dir=DirectionMsg.TRANSMITTED.value,
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

    def _arbitration_id_to_int(self, arbitration_id: str) -> int:
        """
        Convert arbitration ID to int
        """
        if len(arbitration_id) != 8:
            raise ValueError(f"Invalid arbitration ID: {arbitration_id}")
        try:
            arbitration_id = int(arbitration_id, 16)
        except ValueError:
            raise ValueError(f"Invalid arbitration ID: {arbitration_id}")
        return arbitration_id

    def _data_to_bytes(self, data: list[str]) -> bytes:
        """
        Convert data to bytes
        """
        try:
            return bytes.fromhex("".join(data))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid data: {data}")
