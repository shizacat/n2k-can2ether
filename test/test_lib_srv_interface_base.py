import pytest
import can

from pycantoether.lib.srv_interface.base import SrvInterfaceBase


class DummyInterface(SrvInterfaceBase):
    name = "dummy"
    separator = b"|"

    def convert_can_to_srv(self, msg: can.Message) -> bytes:
        return msg.data

    def convert_srv_to_can(self, data: bytes) -> can.Message:
        return can.Message(data=data)


def test_get_interface():
    DummyInterface()  # Registration into `__subclasses__`
    interface = SrvInterfaceBase.get_interface("dummy")
    assert isinstance(interface, DummyInterface)
    assert interface.name == "dummy"


def test_get_interface_unknown():
    with pytest.raises(ValueError, match="Unknown interface: unknown"):
        SrvInterfaceBase.get_interface("unknown")


def test_get_interface_empty():
    with pytest.raises(ValueError, match="Interface name is empty"):
        SrvInterfaceBase.get_interface("")


def test_list_interfaces():
    DummyInterface()  # Registration into `__subclasses__`
    interfaces = SrvInterfaceBase.list_interfaces()
    assert "dummy" in interfaces


def test_convert_can_to_srv():
    dummy = DummyInterface()
    msg = can.Message(data=b"test")
    assert dummy.convert_can_to_srv(msg) == b"test"


def test_convert_srv_to_can():
    dummy = DummyInterface()
    msg = dummy.convert_srv_to_can(b"test")
    assert isinstance(msg, can.Message)
    assert msg.data == b"test"


def test_event_after_process_srv2can():
    dummy = DummyInterface()
    msg = can.Message(data=b"test")
    assert dummy.event_after_process_srv2can(msg) is None
