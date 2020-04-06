import sys
import serial, time, re
from serial.serialutil import SerialException
from optparse import OptionParser


current_version = "v1.0.0"  # changelog in repo

## constants
serial_speeds = {2400: 2, 4800: 4, 9600: 9, 19200: 19, 38400: 38, 57600: 57, 115200: 115}
air_speeds = (4, 8, 16, 24, 32, 64, 96, 128, 192, 250)
netids = range(500)
txpowers = range(1, 31)
default_serial_port = "/dev/ttyUSB0"  # "/dev/ttyMFD2"
DEFAULT_BAUDRATE = 57600

## command line options
parser = OptionParser(usage="%prog serialport_options", version="%prog " + current_version)
parser.add_option("-p", "--port", action="store", type="string", dest="port", help="Serial port. Default: %s" % default_serial_port, default=default_serial_port)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Enables extra information output (debugging).", default="False")
parser.add_option("-t", "--test-baud", action="store_true", dest="test_baud", help="Test serial port for correct baud rate.", default=False)
parser.add_option("-l", "--local", action="store_true", dest="local_radio", help="Work with the local radio. Program default. Can't be used simultaneously with remote option.", default=True)
parser.add_option("-r", "--remote", action="store_false", dest="local_radio", help="Work with the remote radio.")
parser.add_option("--show-parameters", action="store_true", dest="show_parameters", help="Shows all user settable EEPROM parameters.")
parser.add_option("-b", "--baud", action="store", type="int", dest="baud", help="Choose our serial connection speed to the radio in baud. Valid speeds: {}. If no baud specified, it will test. (factory default: {})".format(','.join(map(str, serial_speeds.keys())), DEFAULT_BAUDRATE), default=DEFAULT_BAUDRATE)
parser.add_option("--serial-speed", action="store", type="int", dest="serial_speed", help="Set the radio's serial speed in baud (SERIAL_SPEED).  Valid speeds: {}. (factory default: {}).".format(','.join(map(str, serial_speeds.keys())), DEFAULT_BAUDRATE))
parser.add_option("--adr", action="store", type="int", dest="adr", help="Set the air data rate (AIR_SPEED) in kbps. Valid speeds: " + ', '.join(map(str, air_speeds)) + ". (factory default: 128)")
parser.add_option("--netid", action="store", type="int", dest="netid", help="Set the network ID number (NETID).  Valid IDs: 0 to 499  (factory default: 25)")
parser.add_option("--ecc-on", action="store_true", dest="ecc", help="Enable error correcting code (ECC).")
parser.add_option("--ecc-off", action="store_false", dest="ecc", help="Disable error correcting code (ECC). (factory default)")
parser.add_option("--mavlink-on", action="store_true", dest="mavlink", help="Enable MAVLink framing and reporting (MAVLINK).")
parser.add_option("--mavlink-off", action="store_false", dest="mavlink", help="Disable MAVLink framing and reporting (MAVLINK). (factory default)")
parser.add_option("--or-on", action="store_true", dest="op_resend", help="Enable opportunic resend (OP_RESEND)")
parser.add_option("--or-off", action="store_false", dest="op_resend", help="Disable opportunic resend (OP_RESEND). (factory default)")

(options, args) = parser.parse_args()


## this function lets the program either be terse or speak freely
# use vprint() for verbose messages and print() for standard program output
if options.verbose is True:
    def vprint(*args):
        # Print each argument separately so caller doesn't need to
        # stuff everything to be printed into a single string
        for arg in args:
           print(arg)
else:
    vprint = lambda *a: None      # a do-nothing function


def check_OK(response):
    """Checks for an "OK" response within a string."""
    ok = "OK" in response
    if not ok:
        vprint("ERROR: OK not found in response")
    return ok


def get_response():
    """Gets a response from the serial port."""
    sleep_time_after_buffer_read = 2
    #vprint("Characters in receive buffer before reading:", inBuffer)
    response = b''
    while ser.inWaiting():
        # vprint("Reading serial port buffer.")
        response += ser.readline()
        # vprint("Response:", response.decode('utf-8', errors='ignore'))
        time.sleep(sleep_time_after_buffer_read)
        # vprint("Characters in receive buffer after reading and waiting %d seconds:" % sleep_time_after_buffer_read, ser.inWaiting())
    # vprint("No more characters in serial port buffer.")
    return response.decode('utf-8', errors='ignore')


def command_mode():
    """Enters command mode"""
    ser.flushOutput()
    ser.flushInput()
    time.sleep(1)           # give the flush a second
    ser.write(b'\r\n')  # the ATO command must start on a newline
    vprint("Sent newline and carriage return")
    time.sleep(0.5)
    command = "ATO\r\n"     # exit AT command mode if we are in it
    ser.write(command.encode('utf-8'))
    vprint("Sent command: '{}'".format(command.strip()))
    time.sleep(1)
    command = "ATI\r\n"     # test to see if we are stuck in AT command mode.  If so, we see a response from this.
    vprint("Sent command: '{}'".format(command.strip()))
    time.sleep(1.5)           # minimum 1 second wait needed before +++
    command = "+++"         # +++ enters AT command mode
    ser.write(command.encode('utf-8'))
    vprint("Sent command: '{}'".format(command.strip()))
    time.sleep(2)           # minimum 1 second wait after +++
    response = get_response()
    if check_OK(response):
        return True
    else:
        return False
 
# Notes about serial port modes:
# when opening the serial port,
# possible timeout values:
#    1. None: wait forever, block call
#    2. 0: non-blocking mode, return immediately
#    3. x, x is bigger than 0, float allowed, timeout block call


def test_baud():
    """ tries to connect at each possible baud rate until it gets a successful response """
    for test_baud in sorted(serial_speeds.keys(), reverse=True):
        print("testing baurate at {} ...".format(test_baud))
        ser.baudrate = test_baud
        try:
            ser.open()
        except SerialException:
            print("Couldn't open serial port {}".format(ser.port))
            exit(1)
        vprint("Testing serial port at {} baud.".format(test_baud))
        if command_mode():
            vprint("Test passed at", test_baud, "baud.")
            return(test_baud)   # return the baud value and leave serial port open
        vprint("Test failed at", test_baud, "baud.")
        ser.close()
    vprint("Could not determine baud rate!  Exiting.")
    exit(100)           


if __name__ == "__main__":
    if len(sys.argv) <= 1:  # print help if no argument
        parser.print_help()
        exit(1)
    global ser
    ser = serial.Serial()
    ser.port = options.port
    ser.timeout = 0
    vprint("Serial port is {}".format(ser.port))

    # set for local or remote radio
    if options.local_radio is True:
        command_prefix = "AT"
    else:
        command_prefix = "RT"

    # are we testing for baudrate only?
    if options.test_baud is True:
        baud = test_baud()
        ser.close()
        print("Radio currently working at {} bauds".format(baud))
        exit(0)          # if test_baud was specified, then exit after test

    if options.baud in serial_speeds:
        baud = options.baud
    else:
        vprint(options.baud, " baud is not a valid speed.")
        exit(101)

    ser.baudrate = baud
    vprint("Serial port speed set to", baud, "baud.")

    # print the serial port settings
    vprint("Serial port settings:\n\t", ser)

    # open the serial port
    try:
        ser.open()
    except SerialException:
        print("Couldn't open serial port {}".format(ser.port))
        exit(1)
    vprint("Serial port {} opened.".format(ser.portstr))

    # enter command mode
    if not command_mode():
        print("Couldn't enter command mode")
        print("Check the port and the baudrate (or use -b to detect baudrate)")
        exit(1)

    # flush the input and output buffers
    ser.flushOutput()
    ser.flushInput()
    time.sleep(1)           # give the flush a second. //Reason for this?

    ######
    ## DO ALL THESE THINGS
    ######
    #  0. show parameters
    #  1. set SERIAL_SPEED
    #  2. set AIR_SPEED
    #  3. set NET_ID
    #  4. set TXPOWER
    #  5. set ECC
    #  6. set MAVLINK
    #  7. set OPPRESEND
    #  8. set MIN_FREQ
    #  9. set MAX_FREQ
    # 10. set NUM_CHANNELS
    # 11. set DUTY_CYCLE
    # 12. set LBT_RSSI
    # 13. set MANCHESTER
    # 14. set RTSCTS
    # 15. set NODEID
    # 16. set NODEDESTINATION
    # 17. set SYNCANY
    # 18. set NODECOUNT

    ######
    ##  0. show parameters
    ######
    if options.show_parameters is True:
        vprint("Getting parameters.")
        command = "%sI5\r\n" % command_prefix
        vprint("Sending command: {}".format(command.strip()))
        ser.write(command.encode('utf-8'))
        time.sleep(2)
        response = get_response()
        print(response)
        ser.close()
        exit()

    any_change = False

    ##  1. set SERIAL_SPEED
    if options.serial_speed != None:
        any_change = True
        if int(options.serial_speed) in serial_speeds.keys():
            vprint("Setting SERIAL SPEED to %d baud." % options.serial_speed)
            command = "%sS1=%d\r\n" % (command_prefix, serial_speeds[options.serial_speed])
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if not check_OK(response):
                vprint("Setting serial speed failed. Exiting.")
                exit(102)
        else:
            vprint("Invalid serial speed.")
            exit(103)

    ##  2. set AIR_SPEED
    if options.adr != None:
        any_change = True
        if options.adr in air_speeds:
            vprint("Setting AIR DATA RATE to %dkbit/s." % options.adr)
            command = "%sS2=%d\r\n" % (command_prefix, options.adr)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if not check_OK(response):
                vprint("Setting air data rate failed. Exiting.")
                exit(104)
        else:
            vprint("Invalid air data rate.")
            exit(105)

    ##  3. set NET_ID
    if options.netid != None:
        any_change = True
        if options.netid in netids:
            vprint("Setting network ID (NETID) to %d." % options.netid)
            command = "%sS3=%d\r\n" % (command_prefix, options.netid)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Setting NETID failed. Exiting.")
                exit(106)
        else:
            vprint("Invalid NETID.")
            exit(107)

    #  4. set TXPOWER

    ##  5. set ECC
    if options.ecc != None:
        any_change = True
        if options.ecc is True:
            vprint("Enabling ECC")
            command = "%sS5=1\r\n" % (command_prefix)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not enable ECC. Exiting.")
                exit(108)
        else:
            vprint("Disabling ECC")
            command = "%sS5=0\r\n" % (command_prefix)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not disable ECC. Exiting.")
                exit(109)

    ##  6. set MAVLINK
    if options.mavlink != None:
        any_change = True
        if options.mavlink is True:
            vprint("Enabling MAVLINK")
            command = "%sS6=1\r\n" % (command_prefix)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not enable Mavlink. Exiting.")
                exit(110)
        else:
            vprint("Disabling MAVLINK")
            command = "%sS6=0\r\n" % (command_prefix)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not disable Mavlink. Exiting.")
                exit(111)

    ##  7. set OPPRESEND
    if options.op_resend != None:
        any_change = True
        if options.op_resend is True:
            vprint("Enabling OPPRESEND")
            command = "%sS7=1\r\n" % (command_prefix)
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not enable OPPRESEND. Exiting.")
                exit(112)
        else:
            vprint("Disabling OPPRESEND")
            command = command_prefix + "S7=0\r\n"
            vprint("Sending command: {}".format(command.strip()))
            ser.write(command.encode('utf-8'))
            time.sleep(2)
            response = get_response()
            if  not check_OK(response):
                vprint("Could not disable OPPRESEND. Exiting.")
                exit(113)

    #  8. set MIN_FREQ
    #  9. set MAX_FREQ
    # 10. set NUM_CHANNELS
    # 11. set DUTY_CYCLE
    # 12. set LBT_RSSI
    # 13. set MANCHESTER
    # 14. set RTSCTS
    # 15. set NODEID
    # 16. set NODEDESTINATION
    # 17. set SYNCANY
    # 18. set NODECOUNT

    # write to EEPROM and reboot
    if any_change:
        command = "%s&W\r\n" % command_prefix
        vprint("Sending command: {}".format(command.strip()))
        ser.write(command.encode('utf-8'))
        time.sleep(2)
        response = get_response()
        if not check_OK(response):
            print("ERROR writing parameters in EEPROM")
        command = "%sZ\r\n" % command_prefix
        vprint("Sending command: {}".format(command.strip()))
        ser.write(command.encode('utf-8'))

    # close the serial port
    ser.close()
    vprint("Serial port {} closed.".format(ser.portstr))
