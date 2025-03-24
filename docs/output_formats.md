# Output formats description

## Yacht Devices RAW TCP, ydwg02

[https://www.yachtd.com/downloads/ydwg02.pdf](Documentation)

Format of Messages in RAW Mode
In RAW mode, network messages are converted to plain text format. We recommend that software developers support this format in applications because it is the easiest option. In the terminal window, NMEA 2000 messages look like a log in a chart plotter.

Messages sent from Device to PC have the following form:

```plaintext
hh:mm:ss.ddd D msgid b0 b1 b2 b3 b4 b5 b6 b7<CR><LF>
```

where:
  - hh:mm:sss.ddd — time of message transmission or reception, `ddd` are milliseconds;
  - D — direction of the message («R» — from NMEA 2000 to application, «T» — from application to NMEA 2000);
  - msgid — 29-bit message identifier in hexadecimal format (contains NMEA 2000 PGN and other fields);
  - b0..b7 — message data bytes (from 1 to 8) in hexadecimal format;
  - <CR><LF> — end of line symbols (carriage return and line feed, decimal 13 and 10).

Example:
```plaintext
17:33:21.107 R 19F51323 01 2F 30 70 00 2F 30 70
17:33:21.108 R 19F51323 02 00
17:33:21.141 R 09F80115 A0 7D E6 18 C0 05 FB D5
17:33:21.179 R 09FD0205 64 1E 01 C8 F1 FA FF FF
17:33:21.189 R 1DEFFF00 A0 0B E5 98 F1 08 02 02
17:33:21.190 R 1DEFFF00 A1 00 DF 83 00 00
17:33:21.219 R 15FD0734 FF 02 2B 75 A9 1A FF FF
```

Time of message is UTC time if the Device has received the time from the NMEA 2000 network, otherwise it is the time from Device start.

The format of messages sent from application to Device is the same, but without time and direction field. Outgoing messages must end with <CR><LF>. If the message from application is accepted, passes filters and is transmitted to NMEA 2000, it will be sent back to the application with «T» direction.

For example, the application sends the following sentence to the Device:

```plaintext
19F51323 01 02<CR><LF>
```

When this message is sent to the NMEA 2000 network, the Application receives an answer like:

```plaintext
17:33:21.108 T 19F51323 01 02<CR><LF>
```

The Application will get no answer if the message filtered or the message syntax is invalid.

The format of NMEA 2000 messages is available in Appendix B of NMEA 2000 Standard, which can be purchased on the site https://www.nmea.org/.
