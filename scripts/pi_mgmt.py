import logging
import os
import textwrap
import RPi.GPIO as GPIO
import subprocess

from systemd.journal import JournaldLogHandler


logger = logging.getLogger(__name__)
journald_handler = JournaldLogHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] [+] %(message)s'
))
logger.addHandler(journald_handler)
logger.setLevel(logging.INFO)


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
        logger.setLevel(logging.INFO)
        return "INFO"
    else:
        logger.setLevel(logging.DEBUG)
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
        sudo mv /home/pi/goSecure-master /home/pi/goSecure_Web_GUI
        sudo mv /home/pi/goSecure_Web_GUI.old/ssl.crt /home/pi/goSecure_Web_GUI/.
        sudo mv /home/pi/goSecure_Web_GUI.old/ssl.key /home/pi/goSecure_Web_GUI/.
        sudo mv /home/pi/goSecure_Web_GUI.old/users_db.p /home/pi/goSecure_Web_GUI/.
        sudo chown -R pi:pi /home/pi/goSecure_Web_GUI
        sudo find /home/pi/goSecure_Web_GUI -type d -exec chmod 550 {} \;
        sudo find /home/pi/goSecure_Web_GUI -type f -exec chmod 440 {} \;
        sudo chmod 660 /home/pi/goSecure_Web_GUI/users_db.p
        sudo reboot""")

    for command in update_user_interface_commands.splitlines():
        subprocess.call(command, shell=True)


def turn_led_green(on=True):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(7, GPIO.OUT)
    GPIO.output(7, GPIO.HIGH if on else GPIO.LOW)


def turn_on_led_green():
    logger.debug('called turn_on_led_green()')
    turn_led_green(on=True)


def turn_off_led_green():
    logger.debug('called turn_off_led_green()')
    turn_led_green(on=False)
