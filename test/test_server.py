import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import can

from pycantoether.server import Server
from pycantoether.lib.srv_interface import SrvInterfaceBase


# Create mock interface
class MockInterface(SrvInterfaceBase):
    name = "mock_interface"
    separator = b"|"

    def convert_can_to_srv(self, msg: can.Message) -> bytes:
        return msg.data

    def convert_srv_to_can(self, data: bytes) -> can.Message:
        return can.Message(data=data)


@pytest.fixture
def mock_can_bus() -> AsyncMock:
    """Creates a mock object for can.Bus."""
    with patch("can.Bus") as mock:
        yield mock


@pytest.fixture
def mock_can_notifier() -> AsyncMock:
    """Creates a mock object for can.Notifier."""
    with patch("can.Notifier") as mock:
        yield mock


@pytest.fixture
def server(
    mock_can_bus: AsyncMock, mock_can_notifier: AsyncMock
) -> Server:
    """Creates a server instance with mocked CAN bus and notifier."""
    return Server(
        interface="virtual",
        can_bitrate=250000,
        channel="vcan0",
        srv_interface="mock_interface",
    )


# ==== Tests =====

@pytest.mark.asyncio
async def test_server_start(
    server: Server, mock_can_bus: AsyncMock, mock_can_notifier: AsyncMock
) -> None:
    """Tests successful server startup and CAN initialization."""
    server._can_bus = mock_can_bus
    server._can_notifier = mock_can_notifier

    with patch.object(server, "_server", new=AsyncMock()):
        with patch("asyncio.start_server", new=AsyncMock()):
            task = asyncio.create_task(server._start())
            await asyncio.sleep(0.1)
            task.cancel()

    assert server._can_bus is not None
    assert server._can_notifier is not None


@pytest.mark.asyncio
async def test_can_msg_recipient(server: Server) -> None:
    """Tests the handling of incoming CAN messages."""
    server._srv_client_writers = [AsyncMock()]
    can_msg = MagicMock(arbitration_id=0x123, data=b"test", dlc=4)

    await server._can_msg_recipient(can_msg)

    for writer in server._srv_client_writers:
        writer.write.assert_called()
        writer.drain.assert_called()


# @pytest.mark.asyncio
# async def test_srv_handle(
#     server: Server,
#     mock_can_bus: AsyncMock,
#     mock_can_notifier: AsyncMock
# ) -> None:
#     """Tests the handling of a client connection."""
#     server._can_bus = mock_can_bus
#     server._can_notifier = mock_can_notifier

#     reader = AsyncMock()
#     writer = AsyncMock()
#     reader.readuntil = AsyncMock(return_value=b"test_data")
#     server._srv_client_writers = []

#     with patch.object(
#         server._srv_interface, "convert_srv_to_can", return_value=MagicMock()
#     ):
#         with patch.object(server._can_bus, "send", new=MagicMock()):
#             task = asyncio.create_task(server._srv_handle(reader, writer))
#             await asyncio.sleep(0.1)
#             task.cancel()

#     assert writer in server._srv_client_writers
#     writer.close.assert_called()
#     writer.wait_closed.assert_called()


@pytest.mark.asyncio
async def test_can_close(server: Server) -> None:
    """Tests the closing of the CAN interface."""
    server._can_notifier = MagicMock()
    server._can_bus = MagicMock()

    server._can_close()

    server._can_notifier.stop.assert_called()
    server._can_bus.shutdown.assert_called()
