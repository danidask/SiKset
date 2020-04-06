#!/usr/bin/python

"""A command-line radio setup script for radios with SiK software, like the RFD900 or 3DR."""
# written to communicate with SiK version 2.6 (multipoint firmware)
# written for use with Reach image v1.2
# -which has python 2.7.3
# -and pyserial module version 2.4

current_version = "v0.0.9"
######
## changelog
######
# v0.0.9 updated help, add setting for SERIAL_SPEED, add check-parameters
# v0.0.8 change --set-adr to --adr, add setting for NETID, ECC, MAVLINK, OP_RESEND
# v0.0.7 add differentiation between remote and local radio, and add ability to set air data rate
# v0.0.6 add function to test for correct baud rate
# v0.0.5 add command line options
# v0.0.4 add comments, check if serial port is open
# v0.0.3 interacting with serial port
# v0.0.2 back to basics.  write to port only
# v0.0.1 copy/pasted a function to write to serial port and read back characters


import serial, time, re
from optparse import OptionParser

######
## constants
######
serial_speeds = {2400: 2, 4800: 4, 9600: 9, 19200: 19, 38400: 38, 57600: 57, 115200: 115}
air_speeds = (4, 8, 16, 24, 32, 64, 96, 128, 192, 250)
netids = range(500)
txpowers = range(1,31)
default_serial_port = "/dev/ttyMFD2"

######
## command line options
######
parser = OptionParser(usage="%prog [-p port_filepath] [-b baud]", version="%prog " + current_version)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Enables extra information output (debugging).", default="False")
parser.add_option("-p", "--port", action="store", type="string", dest="port", help="Serial port filepath. Program default: %s" % default_serial_port, default=default_serial_port)
parser.add_option("-t", "--test-baud", action="store_true", dest="test_baud", help="Test serial port for correct baud rate.", default=False)
parser.add_option("-l", "--local", action="store_true", dest="local_radio", help="Work with the local radio. Program default. Can't be used simultaneously with remote option.", default=True)
parser.add_option("-r", "--remote", action="store_false", dest="local_radio", help="Work with the remote radio.")
parser.add_option("--show-parameters", action="store_true", dest="show_parameters", help="Shows all user settable EEPROM parameters.")
parser.add_option("-b", "--baud", action="store", type="int", dest="baud", help="Choose our serial connection speed to the radio in baud.  Valid speeds: %s.  If no baud specified, it will test." % (serial_speeds.keys()) + " (factory default: 57600)", default="0")
parser.add_option("--serial-speed", action="store", type="int", dest="serial_speed", help="Set the radio's serial speed in baud (SERIAL_SPEED).  Valid speeds: %s." % (serial_speeds.keys()) + " (factory default: 57600)", default="0")
parser.add_option("--adr", action="store", type="int", dest="adr", help="Set the air data rate (AIR_SPEED) in kbps. Valid speeds: " + ', '.join(map(str, air_speeds)) + ". (factory default: 128)", default=None)
parser.add_option("--netid", action="store", type="int", dest="netid", help="Set the network ID number (NETID).  Valid IDs: 0 to 499  (factory default: 25)",)
parser.add_option("--ecc-on", action="store_true", dest="ecc", help="Enable error correcting code (ECC).")
parser.add_option("--ecc-off", action="store_false", dest="ecc", help="Disable error correcting code (ECC). (factory default)")
parser.add_option("--mavlink-on", action="store_true", dest="mavlink", help="Enable MAVLink framing and reporting (MAVLINK).")
parser.add_option("--mavlink-off", action="store_false", dest="mavlink", help="Disable MAVLink framing and reporting (MAVLINK). (factory default)")
parser.add_option("--or-on", action="store_true", dest="op_resend", help="Enable opportunic resend (OP_RESEND)")
parser.add_option("--or-off", action="store_false", dest="op_resend", help="Disable opportunic resend (OP_RESEND). (factory default)")

(options, args) = parser.parse_args()


######
## this function lets the program either be terse or speak freely
######
# use vprint() for verbose messages and print() for standard program output
if options.verbose is True:
    def vprint(*args):
        # Print each argument separately so caller doesn't need to
        # stuff everything to be printed into a single string
        for arg in args:
           print arg,
        print
else:   
    vprint = lambda *a: None      # a do-nothing function

######
## this function checks if the respose contains the string "OK"
######

def check_OK(response):
    """Checks for an "OK" response within a string."""
    pattern = '\[[0-9]\]\sOK'
    if re.search(pattern,response):
        return True
    else:
        return False

######
## this function gets a response from the serial port
######

def get_response():
    """Gets a response from the serial port."""
    sleep_time_after_buffer_read = 2
    inBuffer = ser.inWaiting()
    vprint("Characters in receive buffer before reading:", inBuffer)
    response = ""
    while inBuffer > 0:
        vprint("Reading serial port buffer.")
        response = response + ser.readline(inBuffer)
        vprint("Response:", response)
        time.sleep(sleep_time_after_buffer_read)
        inBuffer = ser.inWaiting()
        vprint("Characters in receive buffer after reading and waiting %d seconds:" % sleep_time_after_buffer_read, ser.inWaiting())
    vprint("No more characters in serial port buffer.")
    return response

######
## this function puts the radio in command mode
######
def command_mode():
    """Enters command mode"""
    ser.flushOutput()
    ser.flushInput()
    time.sleep(1)           # give the flush a second
    command = "\r\n"        # the ATO command must start on a newline
    ser.write(command)
    vprint("Sent command: (newline and carriage return)", command)
    time.sleep(0.5)
    command = "ATO\r\n"     # exit AT command mode if we are in it
    ser.write(command)      
    vprint("Sent command:", command)
    time.sleep(1)
    command = "ATI\r\n"     # test to see if we are stuck in AT command mode.  If so, we see a response from this.
    vprint("Sent command:", command)
    time.sleep(2)           # minimum 1 second wait needed before +++
    command = "+++"         # +++ enters AT command mode
    ser.write(command)
    vprint("Sent command:", command)
    time.sleep(5)           # minimum 1 second wait after +++
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

######
## this function tries to connect at each possible baud rate until it gets a sucessful response
######
def test_baud():
    for test_baud in reversed(serial_speeds.keys()):
        ser.baudrate = test_baud
        ser.open()
        vprint("Testing serial port at", test_baud, "baud.")
        if command_mode():
            vprint("Test passed at", test_baud, "baud.")
            return(test_baud)   # return the baud value and leave serial port open
        vprint("Test failed at", test_baud, "baud.")
        ser.close()
    vprint("Could not determine baud rate!  Exiting.")
    exit(100)           

######
## the main program
######
ser = serial.Serial()   # ser is now a global variable
ser.port = options.port
ser.timeout = 0
vprint("Serial port is:", ser.portstr)

# set for local or remote radio
if options.local_radio is True:
    command_prefix = "AT"
else:
    command_prefix = "RT"

# are we testing for baudrate only?
if options.test_baud is True:
    baud = test_baud()
    ser.close()
    print(baud)
    exit(0)          # if test_baud was specified, then exit after test

# was baudrate explicitly set?  if not, test for baudrate
if options.baud == 0:
    baud = test_baud()
else:
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
ser.open()
vprint("Serial port", ser.portstr, "opened.")

# enter command mode
command_mode()

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
    vprint("Sending command: ", command)
    ser.write(command)
    time.sleep(2)
    response = get_response()
    print(response)
    exit()


######
##  1. set SERIAL_SPEED
######

if options.serial_speed != None:
    if options.serial_speed in serial_speeds.keys():
        vprint("Setting SERIAL SPEED to %d baud." % options.serial_speed)
        command = "%sS1=%d\r\n" % (command_prefix, serial_speeds[options.serial_speed])
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Setting serial speed failed. Exiting.")
            exit(102)
    else:
        vprint("Invalid serial speed.")
        exit(103)

######
##  2. set AIR_SPEED
######

if options.adr != None:
    if options.adr in air_speeds:
        vprint("Setting AIR DATA RATE to %dkbit/s." % options.adr)
        command = "%sS2=%d\r\n" % (command_prefix, options.adr)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Setting air data rate failed. Exiting.")
            exit(104)
    else:
        vprint("Invalid air data rate.")
        exit(105)

######
##  3. set NET_ID
######
if options.netid != None:
    if options.netid in netids:
        vprint("Setting network ID (NETID) to %d." % options.netid)
        command = "%sS3=%d\r\n" % (command_prefix, options.netid)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Setting NETID failed. Exiting.")
            exit(106)
    else:
        vprint("Invalid NETID.")
        exit(107)

#  4. set TXPOWER

#####
##  5. set ECC
######

if options.ecc != None:
    if options.ecc is True:
        vprint("Enabling ECC")
        command = "%sS5=1\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Could not enable ECC. Exiting.")
            exit(108)
    else:
        vprint("Disabling ECC")
        command = "%sS5=0\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Could not disable ECC. Exiting.")
            exit(109)
######
##  6. set MAVLINK
######

if options.mavlink != None:
    if options.mavlink is True:
        vprint("Enabling MAVLINK")
        command = "%sS6=1\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Could not enable Mavlink. Exiting.")
            exit(110)
    else:
        vprint("Disabling MAVLINK")
        command = "%sS6=0\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Could not disable Mavlink. Exiting.")
            exit(111)

######
##  7. set OPPRESEND
######

if options.op_resend != None:
    if options.op_resend is True:
        vprint("Enabling OPPRESEND")
        command = "%sS7=1\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
        time.sleep(2)
        response = get_response()
        if  not check_OK(response):
            vprint("Could not enable OPPRESEND. Exiting.")
            exit(112)
    else:
        vprint("Disabling OPPRESEND")
        command = "%sS7=0\r\n" % (command_prefix)
        vprint("Sending command: ", command)
        ser.write(command)
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
command = "%s&W\r\n" % command_prefix
vprint("Sending command: ", command)
ser.write(command)
time.sleep(2)
response = get_response()
check_OK(response)
command = "%sZ\r\n" % command_prefix
vprint("Sending command: ", command)
ser.write(command)

# close the serial port
ser.close()
vprint("Serial port", ser.portstr, "closed.")

