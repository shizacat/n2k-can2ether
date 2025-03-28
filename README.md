# NMEA2000 server

Транслирует данные из NMEA2000 в TCP сервер.

Source:
  - can adapter, GS-USB (Geschwister Schneider). Скажем прошивка - Candle Light.

Трансилируемый формат, выходной формат:
  - Yacht Devices RAW TCP, ydwg02

## Development

```bash
python3 -m venv venv

# install requirements
pip install .
```

## Run, configuration

Config usb.backend libusb1

Environment variables:
- PYUSB_BACKEND - 'libusb1', указывает, что PyUSB должен использовать libusb1.
- LIBUSB_DEBUG - уровень отладки, 0 - 3, 0 = выключено, 3 = максимум.
