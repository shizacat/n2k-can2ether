# The pycantoether

NMEA2000 can bus to TCP server

This is bridge between NMEA2000 and TCP server.

Features:
  - Support different NMEA2000 CAN bus adapters, base on python-can library.
    - GS-USB (Geschwister Schneider), slcan and so on.
  - Support different TCP server interface,
    - Yacht Devices RAW TCP, ydwg02


## Development

```bash
python3 -m venv venv

pip install .
```

## Run, configuration

Config usb.backend libusb1

Environment variables:
- PYUSB_BACKEND - 'libusb1', select libusb1 as backend for PyUSB.
- LIBUSB_DEBUG - debug level, 0 - 3, 0 = off, 3 = max.
