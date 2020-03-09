import logging
import socket
import time
import urllib.request, urllib.error, urllib.parse

from .pi_mgmt import get_output
from . import wifi_captive_portal
from subprocess import CalledProcessError, Popen
from systemd.journal import JournalHandler

logger = logging.getLogger('goSecure')
journald_handler = JournalHandler()
journald_handler.setFormatter(logging.Formatter(
    '[%(levelname)s] [+] %(message)s'
))
logger.addHandler(journald_handler)


def get_wifi_list():
    logger.debug('called get_wifi_list()')
    try:
        wlan_status = get_output(["sudo", "ifup", "wlan0"])
        returncode = 0
    except CalledProcessError as e:
        wlan_status = []
        returncode = e.returncode
    for line in wlan_status:
        logger.debug(line)

    try:
        iw_list = get_output(["sudo", "iwlist", "wlan0", "scan"])
    except CalledProcessError as e:
        iw_list = []
    for line in iw_list:
        logger.debug(line)

    # contains a tuple of the (ESSID, Encryption key)
    wifi_list = []

    for x in range(0, len(iw_list)):
        if (iw_list[x].strip())[0:5] == "ESSID":
            if (iw_list[x].strip())[7:-1] != "" and (not (iw_list[x].strip())[7:-1].startswith("\\")):
                wifi_list.append((((iw_list[x].strip())[7:-1] + "-" + ((iw_list[x-1].strip())[15:])), (iw_list[x].strip())[7:-1]))

    return sorted(list(set(wifi_list)), key=lambda wifilist: wifilist[0])


def add_wifi(wifi_ssid, wifi_key):
    logger.debug('called add_wifi()')
    with open("/etc/wpa_supplicant/wpa_supplicant.conf") as wpa_supplicant:
        lines = wpa_supplicant.readlines()

    wifi_exists = False
    for x in range(0, len(lines)):
        #if SSID is already in file
        if (lines[x].strip()) == 'ssid="' + str(wifi_ssid) + '"':
            wifi_exists = True
            lines[x] = '    ssid="%s"\n' % wifi_ssid
            if wifi_key == "key_mgmt_none":
                lines[x+1] = '    key_mgmt=NONE\n'
            else:
                lines[x+1] = '    psk="%s"\n' % wifi_key

    if wifi_exists is not True:

        lines.append('network={\n')
        lines.append('    ssid="%s"\n' % wifi_ssid)
        if wifi_key == "key_mgmt_none":
            lines.append('    key_mgmt=NONE\n')
        else:
            lines.append('    psk="%s"\n' % wifi_key)
        lines.append('}\n')

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as fout:
        for line in lines:
            fout.write(line)

    process = Popen(["sudo", "ifdown", "wlan0"])
    process.wait()
    process = Popen(["sudo", "ifup", "wlan0"])
    process.wait()

    time.sleep(15)

    if not internet_status():
        wifi_captive_portal.captive_portal(wifi_ssid, "", "")


def ping_status():
    logger.debug('called ping_status()')
    try:
        ping_status = get_output(["ping", "-q", "-c3", "www.google.com"])
        for line in ping_status:
            logger.debug(line)
        return " ".join([line for line in ping_status]).find('3 received') > 0
    except Exception as err:
        pass
    return False

def internet_status():
    logger.debug('called internet_status()')
    try:
        response = urllib.request.urlopen("https://aws.amazon.com", timeout=3)
        return True
    except urllib.error.URLError as err:
        pass
    except socket.timeout as err:
        pass
    return False


def reset_wifi():
    logger.debug('called reset_wifi()')
    lines = ["country=US\n",
             "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n",
             "update_config=1\n"]
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as fout:
        for line in lines:
            fout.write(line)

    try:
        vpn_status = get_output(["sudo", "ifdown", "wlan0"])
        returncode = 0
    except CalledProcessError as e:
        returncode = e.returncode

    return returncode == 0
