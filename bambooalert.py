# Dependencies: python-dateutil
# Activate a dome light every time a build is pushed to CI
# Checks for an email from Bamboo every {checkFrequency} seconds. If an email is present, activate a GPIO pin
# which controls the dome light. Turn off the pin after five seconds.
import dateutil
from dateutil import parser
import json
import urllib.request
import sched, time
import datetime
from subprocess import call
from checkmail import MailChecker
import os.path
import logging

domeLightEvent = None
mailChecker = None
relayDriverPresent = False
s = None    # scheduler instance
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = logging.getLogger("rpi-bamboo-alert")

# check for new builds every X seconds
# Got blocked from mistap.com when I set this to 15
checkFrequency = 60

# turns on dome light
# using a robogaia 4-relay board. dome light is hooked to relay 1.
# http://www.robogaia.com/how-to-add-a-web-interface-to-the-raspberry-pi-4-relay-board.html
def dome_light_on():
    global relayDriverPresent, logger
    if relayDriverPresent:
        call(["relay_on", " 1"])
    else:
        logger.debug("Dome light ON, but relay driver missing")


# turns off dome light
def dome_light_off():
    global relayDriverPresent, logger
    if relayDriverPresent:
        call(["relay_off", " 1"])
    else:
        logger.debug("Dome light OFF, but relay driver missing")

# query Bamboo to see if a new build has been pushed
# if so, activate the dome light
def check_for_new_builds():
    global checkFrequency, domeLightEvent, logger, mailChecker, s
    if mailChecker.check():
        logger.info("New build detected at: ", datetime.datetime.now(), "Activating dome light!")
        dome_light_on()
        # turn dome light off after 5s
        try:
            s.cancel(domeLightEvent)
        except ValueError:
            pass    # this happens if we have not already created an event to turn off the light
        domeLightEvent = s.enter(5, 1, dome_light_off, {})
    s.enter(checkFrequency, 1, check_for_new_builds, {})

# called once at program startup
def init():
    global mailChecker, relayDriverPresent
    filename = "email_credentials.txt"
    mailChecker = MailChecker()
    try:
        mailChecker.load_config_from_file(filename)
    except Exception as e:
        logger.error(e)
        return False

    dome_light_off()
    relayDriverPresent = os.path.isfile("relay_on")
    return True

# main routine starts here
logger.info("Initializing...");
if init():
    logger.info("RPI Bamboo Alert started")
    # interesting: you must have at least one scheduler event setup before you call run()
    # otherwise the script will just exit. maybe I am doing something wrong?
    s = sched.scheduler(time.time, time.sleep)
    s.enter(checkFrequency, 1, check_for_new_builds, {})
    s.run()
