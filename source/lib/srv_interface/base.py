from typing import Optional

import can


class SrvInterfaceBase(object):
    """
    Server interface/protocol base class
    """

    # Interface name, unique
    name: str = ""
    # Separator between messages from application
    separator: bytes = b""

    def convert_can_to_srv(self, msg: can.Message) -> bytes:
        """
        Convert CAN message to server message
        """
        raise NotImplementedError()

    def convert_srv_to_can(self, data: bytes) -> can.Message:
        """
        Convert server message to CAN message
        """
        raise NotImplementedError()

    def event_after_process_srv2can(self, msg: can.Message) -> Optional[bytes]:
        """
        Event after processing server message to CAN message
        """

    @classmethod
    def get_interface(cls, name: str) -> "SrvInterfaceBase":
        """
        Get interface instance

        Raises:
            ValueError: Unknown interface
        """
        if not name:
            raise ValueError("Interface name is empty")
        for cls_ in cls.__subclasses__():
            if cls_.name == name:
                return cls_()
        raise ValueError(f"Unknown interface: {name}")

    @classmethod
    def list_interfaces(cls) -> list[str]:
        """
        Get list of interfaces
        """
        return [cls_.name for cls_ in cls.__subclasses__() if cls_.name]
