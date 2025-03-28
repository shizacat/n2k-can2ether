import datetime

import pytest
import can

from pycantoether.lib.srv_interface.yachtd_raw import YachtdRaw


def test_convert_can_to_srv():
    interface = YachtdRaw()
    msg = can.Message(
        arbitration_id=0x19F51323,
        data=bytes.fromhex("012F3070002F3070"),
        timestamp=datetime.datetime(
            2024, 3, 28, 17, 33, 21, 107000, datetime.UTC
        ).timestamp(),
        is_extended_id=True,
    )
    expected = b"17:33:21.107 R 19F51323 01 2F 30 70 00 2F 30 70\r\n"
    assert interface.convert_can_to_srv(msg) == expected


def test_convert_srv_to_can():
    interface = YachtdRaw()
    data = b"19F51323 01 02\r\n"
    msg = interface.convert_srv_to_can(data)
    assert isinstance(msg, can.Message)
    assert msg.arbitration_id == 0x19F51323
    assert msg.data == bytes.fromhex("0102")
    assert msg.is_extended_id is True


def test_event_after_process_srv2can():
    interface = YachtdRaw()
    msg = can.Message(
        arbitration_id=0x19F51323,
        data=bytes.fromhex("0102"),
        timestamp=datetime.datetime(
            2024, 3, 28, 17, 33, 21, 108000, datetime.UTC
        ).timestamp(),
        is_extended_id=True,
    )
    expected = b"17:33:21.108 T 19F51323 01 02\r\n"
    assert interface.event_after_process_srv2can(msg) == expected


def test_arbitration_id_to_int():
    interface = YachtdRaw()
    assert interface._arbitration_id_to_int("19F51323") == 0x19F51323
    with pytest.raises(ValueError, match="Invalid arbitration ID"):
        interface._arbitration_id_to_int("XYZ12345")
    with pytest.raises(ValueError, match="Invalid arbitration ID"):
        interface._arbitration_id_to_int("123")


def test_data_to_bytes():
    interface = YachtdRaw()
    assert interface._data_to_bytes(["01", "02"]) == bytes.fromhex("0102")
    with pytest.raises(ValueError, match="Invalid data"):
        interface._data_to_bytes(["ZZ"])
    with pytest.raises(ValueError, match="Invalid data"):
        interface._data_to_bytes(["01G2"])
