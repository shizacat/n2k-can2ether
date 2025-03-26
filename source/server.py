#!/usr/bin/env python

"""
CAN server

Channel:
    slcan:
        https://python-can.readthedocs.io/en/stable/interfaces/slcan.html
        port of underlying serial or usb device (e.g. /dev/ttyUSB0, COM8, …)
"""

import sys
import asyncio
import logging
import argparse
from typing import Optional

import can
import usb


class Server(object):

    def __init__(
        self,
        interface: str,
        can_bitrate: int,
        channel: str,
        srv_bind_addr: Optional[str] = None,
        srv_port: Optional[int] = None,
        log_level: str = "ERROR",
    ):
        """
        Args:
            interface: CAN interface for library python-can
            can_bitrate: CAN bitrate, bps
            channel: CAN channel, different for each interface
            srv_bind_addr: server bind address, default 0.0.0.0
            srv_port: server port, default 5000
            log_level: logging level, default ERROR
        """
        self._interface = interface
        self._can_bitrate = can_bitrate
        self._channel = channel

        self._srv_bind_addr = srv_bind_addr if srv_bind_addr else "0.0.0.0"
        self._srv_port = srv_port if srv_port else 5000

        # Logging
        fmt = "%(asctime)s %(levelname)s %(message)s"
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)
        logging.basicConfig(level=log_level, format=fmt)

        # Define variables
        self._server: Optional[asyncio.Server] = None
        self._can_bus: Optional[can.BusABC] = None

        self._event_stop = asyncio.Event()

    def start(self):
        asyncio.run(self._start())

    # Private methods

    async def _start(self):
        """
        Async start server
        """
        # Open CAN bus
        try:
            self._can_bus = can.Bus(
                interface=self._interface,
                bitrate=self._can_bitrate,
                **self._bus_fill_kwargs()
            )
        except usb.core.USBError as e:
            raise RuntimeError(f"CAN bus open error: {e}")

        # Create TCP server
        try:
            self._server = await asyncio.start_server(
                client_connected_cb=self._srv_handle,
                host=self._srv_bind_addr,
                port=self._srv_port,
            )
            self._logger.error(f"Service start on {self._srv_get_bind_addr()}")
        except OSError as e:
            self._can_bus.shutdown()
            raise RuntimeError(f"Service start error: {e}")

        # Wait close
        try:
            await asyncio.Event().wait()
        except asyncio.exceptions.CancelledError:
            self._logger.info("Service stopped")
        self._can_bus.shutdown()

    def _bus_fill_kwargs(self) -> dict:
        """
        Fill kwargs for can.Bus

        Returns:
            dict: kwargs for can.Bus
        """
        kwargs = {}

        # Fill kwargs
        if self._interface == "gs_usb":
            dev = usb.core.find(idVendor=0x1D50, idProduct=0x606F)
            if dev is None:
                raise RuntimeError("Device GS-USB not found")
            kwargs["channel"] = dev.product
            kwargs["index"] = 0
        else:
            kwargs["channel"] = self._channel

        return kwargs

    async def _srv_handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Handle client connection

        Вызывается каждый раз, когда клиент подключается к серверу.
        """
        self._logger.info("Client connected")

        # Read client request
        # data = await reader.read(100)
        # message = data.decode()
        # addr = writer.get_extra_info("peername")

    def _srv_get_bind_addr(self) -> str:
        """
        Get server bind address
        """
        addr = ""

        for sock in self._server.sockets:
            name = sock.getsockname()
            if isinstance(name, tuple) and len(name) == 2:
                item = f"{name[0]}:{name[1]}"
            else:
                item = str(name)
            addr = f"{addr}, {item}" if addr else item
        return addr


def parser_list_interfaces(args: argparse.Namespace):
    """
    List of available interfaces
    """
    print("List of available interfaces:")
    for backend in can.interfaces.BACKENDS:
        print(f"  {backend}")


def cmd_func_run(args: argparse.Namespace):
    """
    Run server
    """
    try:
        server = Server(
            interface=args.interface,
            can_bitrate=args.bitrate,
            channel=args.channel,
            srv_bind_addr=args.bind_addr,
            srv_port=args.port,
            log_level=args.log_level,
        )
        server.start()
    except RuntimeError as e:
        print("Error:", e)
        sys.exit(1)


def arguments(args: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CAN server")

    subparsers = parser.add_subparsers(dest="commands", required=True)

    # List of available backends
    parser_list_interfaces = subparsers.add_parser(
        "list-interfaces", help="List of available interfaces")
    parser_list_interfaces.set_defaults(func=parser_list_interfaces)

    # Run server
    parser_run = subparsers.add_parser("run", help="Run server")
    parser_run.set_defaults(func=cmd_func_run)
    parser_run.add_argument(
        "--interface",
        help="CAN interface",
        type=str,
        required=True,
        choices=can.interfaces.BACKENDS,
    )
    parser_run.add_argument(
        "--bitrate",
        help="CAN bitrate, bps",
        type=int,
        default=250000,
    )
    parser_run.add_argument(
        "--channel",
        help="CAN channel, different for each interface",
        type=str,
        default=""
    )
    # ___ tcp server args ___
    parser_run.add_argument(
        "--bind-addr",
        help="Server bind address, default 0.0.0.0",
        type=str,
        default=None,
    )
    parser_run.add_argument(
        "--port",
        help="Server port, default 5000",
        type=int,
        default=None,
    )
    # ___ General ___
    parser_run.add_argument(
        "--log-level",
        help="Log level",
        type=str,
        default="ERROR",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    return parser.parse_args(args)


if __name__ == '__main__':
    # Test on gs_usb
    args = arguments()
    args.func(args)
