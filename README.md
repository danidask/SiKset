# SiKset

A command-line radio setup script for radios with SiK software, like the RFD900 or 3DR.
written to communicate with SiK version 2.6 (multipoint firmware)


# command line options

```
Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -p PORT, --port=PORT  Serial port. Default: /dev/ttyUSB0
  -v, --verbose         Enables extra information output (debugging).
  -t, --test-baud       Test serial port for correct baud rate.
  -l, --local           Work with the local radio. Program default. Can't be
                        used simultaneously with remote option.
  -r, --remote          Work with the remote radio.
  --show-parameters     Shows all user settable EEPROM parameters.
  -b BAUD, --baud=BAUD  Choose our serial connection speed to the radio in
                        baud. Valid speeds:
                        2400,4800,9600,19200,38400,57600,115200. If no baud
                        specified, it will test. (factory default: 57600)
  --serial-speed=SERIAL_SPEED
                        Set the radio's serial speed in baud (SERIAL_SPEED).
                        Valid speeds: 2400,4800,9600,19200,38400,57600,115200.
                        (factory default: 57600).
  --adr=ADR             Set the air data rate (AIR_SPEED) in kbps. Valid
                        speeds: 4, 8, 16, 24, 32, 64, 96, 128, 192, 250.
                        (factory default: 128)
  --netid=NETID         Set the network ID number (NETID).  Valid IDs: 0 to
                        499  (factory default: 25)
  --ecc-on              Enable error correcting code (ECC).
  --ecc-off             Disable error correcting code (ECC). (factory default)
  --mavlink-on          Enable MAVLink framing and reporting (MAVLINK).
  --mavlink-off         Disable MAVLink framing and reporting (MAVLINK).
                        (factory default)
  --or-on               Enable opportunic resend (OP_RESEND)
  --or-off              Disable opportunic resend (OP_RESEND). (factory
                        default)
```

# examples

Find out the actual baudrate of the radio
`python SiKset.py -p /dev/ttyUSB0 --test-baud`

Useful radio info
`python SiKset.py -p /dev/ttyUSB0 -b 57600 --show-parameters`

Change baudrate radio from 57600 to 9600
`python SiKset.py -p /dev/ttyUSB0 -b 57600 --serial-speed=9600`

Disable remote radio ECC:
`python SiKset.py -p /dev/ttyUSB0 --remote --ecc-off`


# requirements

python 3
pyserial (pip install pyserial)


# References 

I found this script [here](https://community.emlid.com/t/sikset-py-a-python-script-to-easily-control-your-rfd900-3dr-radio-from-the-command-line/3654) and continue at this point. Thanks to the user <b>Bide</b>

https://ardupilot.org/copter/docs/common-3dr-radio-advanced-configuration-and-technical-information.html
