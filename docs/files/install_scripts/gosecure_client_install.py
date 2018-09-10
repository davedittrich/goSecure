#!/usr/bin/env python3

import os
import sys
import textwrap
import time
from subprocess import call, check_output


def update_os():
    print("goSecure_Client_Script - Update OS\n")
    call("sudo apt-get update", shell=True)
    call("sudo apt-get upgrade -y", shell=True)
    call("sudo apt-get install tree dnsutils byobu gpm unzip -y", shell=True)


def update_python3():
    print("goSecure_Client_Script - Install Python3.6\n")
    call("sudo apt-get update", shell=True)
    call("sudo apt-get install build-essential checkinstall " +
         "libreadline-gplv2-dev libncursesw5-dev libssl-dev " +
         "libsqlite3-dev tk-dev libc6-dev libbz2-dev -y", shell=True)
    call("sudo wget https://www.python.org/ftp/python/3.6.5/" +
         "Python-3.6.5.tgz -O /usr/src/Python-3.6.5.tgz", shell=True)
    call("sudo sh -c 'cd /usr/src; "  +
         "tar -xzf /usr/src/Python-3.6.5.tgz; " +
         "cd Python-3.6.5; " +
         "./configure; " +
         "make altinstall;" +
         "/usr/local/bin/python3.6 -m pip install -U pip'", shell=True)
    # TODO(dittrich): Not working...no time to fix
    #call("test \"$(python3.6 -V)\" == \"Python 3.6.5\"", shell=True)


def enable_ip_forward():
    print("goSecure_Client_Script - Enable IP Forwarding\n")
    call("sudo sh -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'", shell=True)

    with open("/etc/sysctl.conf") as fin:
        lines = fin.readlines()

    for i, line in enumerate(lines):
        if "net.ipv4.ip_forward" in line:
            lines[i] = "net.ipv4.ip_forward = 1\n"

    with open("/etc/sysctl.conf", "w") as fout:
        for line in lines:
            fout.write(line)

    call("sudo sysctl -p", shell=True)


def configure_firewall():
    print("goSecure_Client_Script - Configure Firewall\n")
    if not os.path.exists('/etc/iptables'):
        call("sudo mkdir /etc/iptables/", shell=True)

    iptables_rules = textwrap.dedent("""\
        *mangle
        :PREROUTING ACCEPT [0:0]
        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        -A FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1300
        COMMIT

        *filter
        :INPUT DROP [0:0]
        :FORWARD DROP [0:0]
        :OUTPUT ACCEPT [0:0]
        -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        -A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
        -A INPUT -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT
        -A INPUT -m udp -p udp --dport 53 -j ACCEPT
        -A INPUT -m udp -p udp --dport 67 -j ACCEPT
        -A INPUT -m udp -p udp --dport 68 -j ACCEPT
        -A FORWARD -i ipsec0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
        -A FORWARD -i eth0 -o ipsec0 -j ACCEPT
        COMMIT

        *nat
        :PREROUTING ACCEPT [0:0]
        :INPUT ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        -A POSTROUTING -o ipsec0 -j MASQUERADE
        COMMIT
        """)

    iptables_file = open("/etc/iptables/rules.v4", "w")
    iptables_file.write(iptables_rules)
    iptables_file.close()

    iptables_start_on_boot_script = textwrap.dedent("""\
        #!/bin/sh
        sudo /sbin/iptables-restore < /etc/iptables/rules.v4\n""")

    iptables_start_on_boot_file = open("/etc/network/if-pre-up.d/firewall", "w")
    iptables_start_on_boot_file.write(iptables_start_on_boot_script)
    iptables_start_on_boot_file.close()

    call("sudo chmod 550 /etc/network/if-pre-up.d/firewall", shell=True)


def enable_hardware_random():
    print("goSecure_Client_Script - Enable Hardware Random\n")
    call("sudo apt-get install rng-tools -y", shell=True)
    call("sudo systemctl enable rng-tools", shell=True)


def install_strongswan():
    print("goSecure_Client_Script - Install strongSwan\n")
    install_strongswan_commands = textwrap.dedent("""\
        sudo apt-get install -y libssl-dev libpam-dev
        wget -P /tmp https://download.strongswan.org/strongswan-5.5.0.tar.gz
        tar -xvzf /tmp/strongswan-5.5.0.tar.gz -C /tmp
        cd /tmp/strongswan-5.5.0/ && ./configure --prefix=/usr --sysconfdir=/etc --enable-gcm --with-random-device=/dev/hwrng --enable-kernel-libipsec --enable-openssl --with-fips-mode=2 --disable-vici --disable-des --disable-ikev2 --disable-gmp
        make -C /tmp/strongswan-5.5.0/
        sudo make -C /tmp/strongswan-5.5.0/ install""")

    for command in install_strongswan_commands.splitlines():
        call(command, shell=True)

def configure_strongswan():
    print("goSecure_Client_Script - Configure strongSwan\n")

    # https://www.blackhole-networks.com/IKE_Modes/ikev1-aggressive-weakness.html
    strongswan_conf = textwrap.dedent("""\
        charon {
                interfaces_use = wlan0 # the external/WAN interface
                load_modular = yes
                i_dont_care_about_security_and_use_aggressive_mode_psk=yes
                plugins {
                        include strongswan.d/charon/*.conf
                }
        }

        include strongswan.d/*.conf""")

    with open("/etc/strongswan.conf", "w") as f:
        f.write(strongswan_conf)

    ipsec_conf = textwrap.dedent("""\
        config setup

        conn %default
                ikelifetime=60m
                keylife=20m
                rekeymargin=3m
                keyingtries=1
                keyexchange=ikev1

        conn work
                left=%defaultroute      # external IP address
                leftsourceip=%config    # external IP address
                leftid=<unique_id_of_client>   # unique id of client i.e. client1@d2.local
                leftfirewall=yes        # automatically add firewall rules
                right=<eth0_ip_of_server>       # strongSwan server external IP or DNS name
                rightsubnet=0.0.0.0/0     # route all traffic to the strongSwan server
                rightid=@gosecure     # unique id of server
                auto=start      # start tunnel when strongSwan service starts
                authby=secret
                ike=aes256-sha384-ecp384!
                esp=aes256gcm128!
                aggressive=yes # this is required to support multiple road warrior clients that use just a pre-shared key.""")

    with open("/etc/ipsec.conf", "w") as f:
        f.write(ipsec_conf)

    ipsec_secrets = "<unique_id_of_client> : PSK <password_for_client>"

    with open("/etc/ipsec.secrets", "w") as f:
        f.write(ipsec_secrets)

    with open("/etc/strongswan.d/charon/openssl.conf") as fin:
        lines = fin.readlines()

    for i, line in enumerate(lines):
        if "fips_mode = 0" in line:
            lines[i] = "    fips_mode = 0\n"

    with open("/etc/strongswan.d/charon/openssl.conf", "w") as fout:
        fout.writelines(line)

    call("sudo service networking restart", shell=True)
    time.sleep(30)

def start_strongswan():
    print("goSecure_Client_Script - Start strongSwan\n")

    # start strongSwan
    call("sudo ipsec start", shell=True)

    # start strongSwan on boot
    with open("/etc/network/if-pre-up.d/firewall", "r") as f:
        for line in f:
            if "sudo ipsec start" in line:
                break
        else: # not found, we are at the eof
            call("sudo sh -c 'echo \"sudo ipsec start\" >> /etc/network/if-pre-up.d/firewall'", shell=True)

    # add temporary route for local eth0 interface
    call("sudo ip route add table 220 192.168.50.0/24 dev eth0", shell=True)

    if not os.path.exists('/etc/rc.local'):
        call("sudo sh -c \"echo '#!/bin/sh -e' > /etc/rc.local\"", shell=True)
        call("sudo chmod 755 /etc/rc.local", shell=True)

    # TODO(dittrich): This is a hack to get LED functioning.
    # The /etc/rc.local file should be properly templated (e.g., with Jinja)
    route_on_boot_commands = textwrap.dedent("""\
        sudo sed -i '$ d' /etc/rc.local
        sudo sh -c \"echo 'ip route add table 220 192.168.50.0/24 dev eth0' >> /etc/rc.local\"
        sudo sh -c \"echo 'echo none > /sys/class/leds/led0/trigger' >> /etc/rc.local\"
        sudo sh -c \"echo 'exit 0' >> /etc/rc.local\"
        """)

    # add route on boot
    with open("/etc/rc.local", "r+") as f:
        for line in f:
            if "ip route add table 220 192.168.50.0/24 dev eth0" in line:
                break

        else: # not found, we are at the eof
            for command in route_on_boot_commands.splitlines():
                call(command, shell=True)

def setup_dhcp_and_dns_server():
    print("goSecure_Client_Script - Setup DHCP and DNS Server\n")
    call("sudo apt-get update", shell=True)
    call("sudo apt-get -o Dpkg::Options::='--force-confdef' " +
         "-o Dpkg::Options::='--force-confold' " +
         "install dnsmasq -y", shell=True)

    dhcp_and_dns_conf = textwrap.dedent("""\
        ######## dns ########
        # Never forward plain names (without a dot or domain part)
        domain-needed
        # Never forward addresses in the non-routed address spaces
        bogus-priv
        # don't read resolv.conf   use the defined servers instead
        # no-resolv
        server=8.8.8.8
        server=8.8.4.4
        # increase dns cache form 512 to 4096
        cache-size=4096

        ######### dhcp ##########
        # Add local-only domains here, queries in these domains are answered
        # from /etc/hosts or DHCP only
        local=/home/
        # Set this (and domain: see below) if you want to have a domain
        # automatically added to simple names in a hosts-file.
        expand-hosts
        # adds my localdomain to each dhcp host
        domain=gosecure
        # my private dhcp range + subnetmask + 14d lease time
        dhcp-range=192.168.50.101,192.168.50.200,255.255.255.0,14d
        # set route to my local network router
        dhcp-option=option:router,192.168.50.1
        # windows 7 float fix
        dhcp-option=252,"\\n"

        ###### logging ############
        # own logfile
        log-facility=/var/log/dnsmasq.log
        log-async
        # log dhcp infos
        log-dhcp
        # debugging dns
        # log-queries""")

    with open("/etc/dnsmasq.conf", "w") as f:
        f.write(dhcp_and_dns_conf)

    # call("sudo sh -c 'echo \"192.168.50.1 setup\" >> /etc/hosts'", shell=True)
    # add domain name to local dns lookup file
    dns = "192.168.50.1 setup"
    with open("/etc/hosts", "a+") as f:
        f.seek(0)
        if not any(dns == x.rstrip() for x in f):
            f.write(dns + '\n')

    call("sudo systemctl enable dnsmasq", shell=True)
    call("sudo systemctl start dnsmasq", shell=True)

def setup_user_interface():
    print("goSecure_Client_Script - Setup User Interface\n")
    setup_user_interface_commands = textwrap.dedent("""\
        sudo apt-get install libsystemd-dev libxslt1-dev libyaml-dev libxml2-dev -y
        sudo /usr/local/bin/python3.6 -m pip install RPi.GPIO systemd Flask Flask-WTF Flask-Login mechanicalsoup
        wget -P /home/pi https://github.com/davedittrich/goSecure/archive/master.zip
        unzip /home/pi/master.zip
        rm /home/pi/master.zip
        sudo mv /home/pi/goSecure-master /home/pi/goSecure_Web_GUI
        sudo chown -R pi:pi /home/pi/goSecure_Web_GUI
        sudo find /home/pi/goSecure_Web_GUI -type d -exec chmod 550 {} \;
        sudo find /home/pi/goSecure_Web_GUI -type f -exec chmod 440 {} \;
        sudo chmod 550 /home/pi/goSecure_Web_GUI/gosecure_app.py
        sudo chmod 660 /home/pi/goSecure_Web_GUI/users_db.p""")

    for command in setup_user_interface_commands.splitlines():
        call(command, shell=True)

    gosecure_service_conf = textwrap.dedent("""\
        [Unit]
        Description=goSecure Web GUI Service
        Wants=network-online.target
        After=network.target network-online.target

        [Service]
        Type=idle
        ExecStart=/usr/local/bin/python3.6 /home/pi/goSecure_Web_GUI/gosecure_app.py

        [Install]
        WantedBy=default.target""")

    with open("/lib/systemd/system/gosecure.service", "w") as f:
        f.write(gosecure_service_conf)

    setup_gosecure_service_commands = textwrap.dedent("""\
        sudo chmod 644 /lib/systemd/system/gosecure.service
        sudo systemctl daemon-reload
        sudo systemctl enable gosecure.service""")

    for command in setup_gosecure_service_commands.splitlines():
        call(command, shell=True)


def main():
    cmdargs = str(sys.argv)
    if len(sys.argv) != 1:
        print('Syntax is: sudo python3 gosecure_client_install.py\nExample: sudo python3 gosecure_client_install.py\n')
        exit()

    call("sh -c 'date +%s > /home/pi/.install-started'", shell=True)
    update_os()
    enable_hardware_random()
    update_python3()
    enable_ip_forward()
    configure_firewall()
    setup_dhcp_and_dns_server()
    setup_user_interface()
    install_strongswan()
    configure_strongswan()
    start_strongswan()
    call("sh -c 'date +%s > /home/pi/.install-finished'", shell=True)

    call("echo 'Rebooting now... please wait 30-60 seconds and navigate to https://setup.gosecure'", shell=True)
    time.sleep(10)
    call("sudo shutdown -r now", shell=True)

if __name__ == "__main__":
    main()
