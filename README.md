# The pycantoether

NMEA2000 can bus to TCP server

This is bridge between NMEA2000 and TCP server.

Features:
  - Support different NMEA2000 CAN bus adapters, base on python-can library.
    - GS-USB (Geschwister Schneider), slcan and so on.
  - Support different TCP server interface,
    - Yacht Devices RAW TCP, ydwg02

Requirements:
  - python 3.9+

## Install

```bash
pip install pycantoether
```

[Usage](docs/01.usage.md)

## Development

```bash
python3 -m venv venv
source venv/bin/activate

# Install requirements, and editable this package
pip install -e .
```

## Run, configuration

Config usb.backend libusb1

Environment variables:
- PYUSB_BACKEND - 'libusb1', select libusb1 as backend for PyUSB.
- LIBUSB_DEBUG - debug level, 0 - 3, 0 = off, 3 = max.
