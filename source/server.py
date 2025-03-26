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
from enum import Enum
from typing import Optional

import can
import usb


class Server(object):

    def __init__(
        self,
        interface: str,
        can_bitrate: int,
        channel: str,
    ):
        """
        Args:
            interface: CAN interface for library python-can
            can_bitrate: CAN bitrate, bps
            channel: CAN channel, different for each interface
        """
        self._interface = interface
        self._can_bitrate = can_bitrate
        self._channel = channel

    def start(self):
        bus = can.Bus(
            interface=self._interface,
            bitrate=self._can_bitrate,
            **self._bus_fill_kwargs()
        )

        # Process
        # ...

        # Correct close bus
        bus.shutdown()

    # Private methods

    def _bus_fill_kwargs(self) -> dict:
        """
        Fill kwargs for can.Bus
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

    return parser.parse_args(args)


if __name__ == '__main__':
    # Test on gs_usb
    args = arguments()
    args.func(args)
