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

from .lib.srv_interface import SrvInterfaceBase


class Server(object):

    def __init__(
        self,
        interface: str,
        can_bitrate: int,
        channel: str,
        srv_interface: str,
        srv_bind_addr: Optional[str] = None,
        srv_port: Optional[int] = None,
        log_level: str = "ERROR",
    ):
        """
        Args:
            interface: CAN interface for library python-can
            can_bitrate: CAN bitrate, bps
            channel: CAN channel, different for each interface
            srv_interface: server interface
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

        # Server interface
        self._srv_interface = SrvInterfaceBase.get_interface(srv_interface)
        self._logger.info(f"Server interface: {self._srv_interface.name}")

        # Define variables
        self._server: Optional[asyncio.Server] = None
        self._can_bus: Optional[can.BusABC] = None
        self._can_notifier: Optional[can.Notifier] = None

        # __
        self._event_stop = asyncio.Event()
        # List of clients writer
        self._srv_client_writers: list[asyncio.StreamWriter] = []

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
                receive_own_messages=False,
                **self._bus_fill_kwargs()
            )
            self._can_notifier = can.Notifier(
                bus=self._can_bus,
                listeners=[self._can_msg_recipient],
                loop=asyncio.get_running_loop(),
            )
        except (usb.core.USBError, can.exceptions.CanError) as e:
            raise RuntimeError(f"CAN bus open error: {e}")

        # Create TCP server
        try:
            self._server = await asyncio.start_server(
                client_connected_cb=self._srv_handle,
                host=self._srv_bind_addr,
                port=self._srv_port,
            )
            self._logger.info(f"Service start on {self._srv_get_bind_addr()}")
        except OSError as e:
            self._can_close()
            raise RuntimeError(f"Service start error: {e}")

        # Wait close
        try:
            await asyncio.Event().wait()
        except asyncio.exceptions.CancelledError:
            self._logger.info("Service stopped")
        self._can_close()

    def _can_close(self):
        """
        Close CAN bus
        """
        try:
            self._can_notifier.stop()
            self._can_bus.shutdown()
        except can.exceptions.CanOperationError as e:
            self._logger.error(f"CAN bus close error: {e}")

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
        addr = writer.get_extra_info("peername")

        self._logger.info(f"Client connected: address={addr}")

        # Setup
        self._srv_client_writers.append(writer)

        try:
            while True:
                # Читаем данные от клиента
                # # TODO: asyncio.exceptions.IncompleteReadError, check
                data = await reader.readuntil(
                    separator=self._srv_interface.separator)

                self._logger.debug(f"Received data: {data}")
                try:
                    can_msg = self._srv_interface.convert_srv_to_can(data)
                except ValueError as e:
                    self._logger.error(f"Invalid data: {e}")
                    continue

                # Send message to CAN bus
                try:
                    self._can_bus.send(can_msg, timeout=1)
                except can.exceptions.CanError as e:
                    self._logger.error(f"CAN bus send error: {e}")
                    continue

                # Event after process
                data_after = self._srv_interface.event_after_process_srv2can(
                    can_msg)
                if data_after:
                    writer.write(data_after)
                    await writer.drain()
        except asyncio.CancelledError:
            pass  # Разрешаем корректное завершение
        finally:
            self._logger.info(f"Client disconnected: {addr}")
            self._srv_client_writers.remove(writer)
            writer.close()
            await writer.wait_closed()  # Закрываем соединение

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

    async def _can_msg_recipient(self, msg: can.Message):
        """
        Get recipient message from CAN bus
        """
        self._logger.debug(
            f"Received message: ID: {msg.arbitration_id:08X}, "
            f"Data: {msg.data.hex()}, DLC: {msg.dlc}"
        )
        # Send message to srv clients
        for writer in self._srv_client_writers:
            writer.write(self._srv_interface.convert_can_to_srv(msg))
            await writer.drain()


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
            srv_interface=args.srv_interface,
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
    # ___ can args ___
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
    parser_run.add_argument(
        "--srv-interface",
        help="Server interface",
        type=str,
        required=True,
        choices=SrvInterfaceBase.list_interfaces(),
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


def main():
    args = arguments()
    args.func(args)


if __name__ == '__main__':
    main()
