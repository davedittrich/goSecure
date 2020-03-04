import logging
import os
import textwrap
import RPi.GPIO as GPIO
import subprocess

from systemd.journal import JournalHandler


logger = logging.getLogger('goSecure')
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] [+] %(message)s'
))
logger.addHandler(journald_handler)


def get_output(cmd=['echo', 'NO COMMAND SPECIFIED']):
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT
        ).decode('UTF-8').splitlines()
    return output


def pi_reboot():
    logger.debug('called pi_reboot()')
    os.system("sudo reboot")


def pi_shutdown():
    logger.debug('called pi_shutdown()')
    os.system("sudo shutdown -h now")


def toggle_logging():
    """Toggle logging level between INFO (default) and DEBUG"""
    logger.debug('called toggle_logging()')
    current = logger.getEffectiveLevel()
    if current == logging.DEBUG:
        logger.debug('logging level now INFO')
        logger.setLevel(logging.INFO)
        return "INFO"
    else:
        logger.setLevel(logging.DEBUG)
        logger.debug('logging level now DEBUG')
        return "DEBUG"

def start_ssh_service():
    logger.debug('called start_ssh_service()')
    os.system("sudo service ssh start")


def update_client():
    logger.debug('called update_client()')
    update_user_interface_commands = textwrap.dedent("""\
        sudo mv /home/pi/goSecure_Web_GUI /home/pi/goSecure_Web_GUI.old
        wget -P /home/pi/. https://github.com/davedittrich/goSecure/archive/master.zip
        unzip -d /home/pi/. /home/pi/master.zip
        rm /home/pi/master.zip
        sudo chown -R pi:pi /home/pi/goSecure-master
        sudo find /home/pi/goSecure-master -type d -exec chmod 550 {} \;
        sudo find /home/pi/goSecure-master_-type f -exec chmod 440 {} \;
        sudo mv /home/pi/goSecure-master /home/pi/goSecure_Web_GUI
        sudo mv /home/pi/goSecure_Web_GUI.old/ssl.crt /home/pi/goSecure_Web_GUI/.
        sudo mv /home/pi/goSecure_Web_GUI.old/ssl.key /home/pi/goSecure_Web_GUI/.
        sudo mv /home/pi/goSecure_Web_GUI.old/users_db.p /home/pi/goSecure_Web_GUI/.
        sudo chmod 660 /home/pi/goSecure_Web_GUI/users_db.p
        sudo chown -R pi:pi /home/pi/goSecure_Web_GUI
        sudo find /home/pi/goSecure_Web_GUI -type d -exec chmod 550 {} \;
        sudo find /home/pi/goSecure_Web_GUI -type f -exec chmod 440 {} \;
        sudo shutdown -r now""")

    for command in update_user_interface_commands.splitlines():
        subprocess.call(command, shell=True)

# See: https://www.raspberrypi-spy.co.uk/2012/09/checking-your-raspberry-pi-board-version/
def turn_led_green(on=True):
    state = 1 if on else 0
    # TODO(dittrich): Add support for differentiating RPi type to use this
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setwarnings(False)
    #GPIO.setup(7, GPIO.OUT)
    #GPIO.output(7, GPIO.HIGH if on else GPIO.LOW)
    # Works on "Raspberry Pi 3 Model B Plus Rev 1.3" per /proc/device-tree/model
    get_output(['/opt/vc/bin/vcmailbox', '0x00038040', '8', '8', '130',
        str(state)])


def turn_on_led_green():
    logger.debug('called turn_on_led_green()')
    turn_led_green(on=True)


def turn_off_led_green():
    logger.debug('called turn_off_led_green()')
    turn_led_green(on=False)
