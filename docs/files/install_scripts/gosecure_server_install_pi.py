#!/usr/bin/env python3

import sys
import textwrap
import time
from subprocess import call, check_output


def update_os():
    print("goSecure_Server_Script - Update OS\n")
    call("sudo apt-get update", shell=True)
    call("sudo apt-get upgrade -y", shell=True)
    call("sudo apt-get install tree dnsutils byobu gpm unzip -y", shell=True)


def update_python3():
    print("goSecure_Server_Script - Install Python3.6\n")
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
    print("goSecure_Server_Script - Enable IP Forwarding\n")
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
    print("goSecure_Server_Script - Configure Firewall\n")
    call("sudo mkdir /etc/iptables/", shell=True)

    iptables_rules = textwrap.dedent("""\
        *filter
        :INPUT DROP [0:0]
        :FORWARD DROP [0:0]
        :OUTPUT ACCEPT [0:0]
        -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        # -A INPUT -p icmp -j ACCEPT
        -A INPUT -i lo -j ACCEPT
        -A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
        -A INPUT -m udp -p udp --dport 500 -j ACCEPT
        -A INPUT -m udp -p udp --dport 4500 -j ACCEPT
        -A FORWARD -i eth0 -o eth1 -j ACCEPT
        -A FORWARD -i eth1 -o eth0 -j ACCEPT
        -A FORWARD -i ipsec0 -o eth0 -j ACCEPT
        -A FORWARD -i eth0 -o ipsec0 -j ACCEPT
        -A FORWARD -i ipsec0 -o eth1 -j ACCEPT
        -A FORWARD -i eth1 -o ipsec0 -j ACCEPT
        -A INPUT -j REJECT --reject-with icmp-host-prohibited
        -A FORWARD -j REJECT --reject-with icmp-host-prohibited
        COMMIT

        *nat
        :PREROUTING ACCEPT [0:0]
        :POSTROUTING ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        -A POSTROUTING -o eth0 -j MASQUERADE
        -A POSTROUTING -o eth1 -j MASQUERADE
        COMMIT\n""")

    iptables_file = open("/etc/iptables/rules.v4", "w")
    iptables_file.write(iptables_rules)
    iptables_file.close()

    iptables_start_on_boot_script = textwrap.dedent("""\
        #!/bin/sh
        sudo ifdown wlan0
        sudo /sbin/iptables-restore < /etc/iptables/rules.v4\n""")

    iptables_start_on_boot_file = open("/etc/network/if-pre-up.d/firewall", "w")
    iptables_start_on_boot_file.write(iptables_start_on_boot_script)
    iptables_start_on_boot_file.close()

    call("sudo chmod 550 /etc/network/if-pre-up.d/firewall", shell=True)


def enable_hardware_random():
    print("goSecure_Server_Script - Enable Hardware Random\n")
    call("sudo apt-get install rng-tools -y", shell=True)
    call("sudo systemctl enable rng-tools", shell=True)


def install_strongswan():
    print("goSecure_Client_Script - Install strongSwan\n")
    install_strongswan_commands = textwrap.dedent("""\
        sudo apt-get install -y libssl-dev libpam-dev
        wget -P /tmp https://download.strongswan.org/strongswan-5.5.0.tar.gz
        tar -xvzf /tmp/strongswan-5.5.0.tar.gz -C /tmp
        cd /tmp/strongswan-5.5.0/ && ./configure --prefix=/usr --sysconfdir=/etc --enable-gcm --with-random-device=/dev/hwrng --enable-kernel-libipsec --enable-openssl --with-fips-mode=2 --disable-vici --disable-des --disable-ikev2 --disable-gmp --enable-systemd --enable-swanctl
        make -C /tmp/strongswan-5.5.0/
        sudo make -C /tmp/strongswan-5.5.0/ install""")

    for command in install_strongswan_commands.splitlines():
        call(command, shell=True)


def configure_strongswan(client_id=None, client_psk=None):
    print("goSecure_Server_Script - Configure strongSwan\n")

    # TODO(dittrich): Fix this
    # https://www.blackhole-networks.com/IKE_Modes/ikev1-aggressive-weakness.html
    strongswan_conf = textwrap.dedent("""\
        charon {
                interfaces_use = eth0
                load_modular = yes
                i_dont_care_about_security_and_use_aggressive_mode_psk=yes
                plugins {
                        include strongswan.d/charon/*.conf
                }
        }

        include strongswan.d/*.conf""")

    with open("/etc/strongswan.conf", "w") as f:
        f.write(strongswan_conf)

    # DEPRECATED: Moving this to cloud-config.server.j2 file
    if not (client_id is None and client_psk is None):
        ipsec_conf = textwrap.dedent("""\
            config setup

            conn %default
                    ikelifetime=60m
                    keylife=20m
                    rekeymargin=3m
                    keyingtries=1
                    keyexchange=ikev1
                    left=%defaultroute
                    leftsubnet=0.0.0.0/0
                    leftid=@gosecure
                    leftfirewall=yes
                    right=%any
                    rightsourceip=172.16.176.100/27
                    auto=add
                    authby=secret
                    ike=aes256-sha384-ecp384!
                    esp=aes256gcm128!
                    aggressive=yes


            conn rw-client1
                    rightid={0}

            # To add additional clients:
            # conn rw-client2 # increment the last number by 1 for each additional client
            #        rightid=<unique_id_of_client> # set a unique id for each client""".format(client_id))

        with open("/etc/ipsec.conf", "w") as f:
            f.write(ipsec_conf)
        ipsec_conf_file.close()

        ipsec_secrets = "{0} : PSK {1}".format(client_id, client_psk)

        with open("/etc/ipsec.secrets", "w") as f:
            f.write(ipsec_secrets)

    with open("/etc/strongswan.d/charon/openssl.conf") as fin:
        lines = fin.readlines()

    for i, line in enumerate(lines):
        if "fips_mode = 0" in line:
            lines[i] = "    fips_mode = 0\n"

    with open("/etc/strongswan.d/charon/openssl.conf", "w") as fout:
        for line in lines:
            fout.write(line)

    call("sudo service networking restart", shell=True)
    time.sleep(30)

def start_strongswan():
    print("goSecure_Server_Script - Start strongSwan\n")

    # start strongSwan
    call("sudo ipsec start", shell=True)

    # start strongSwan on boot
    with open("/etc/network/if-pre-up.d/firewall", "r") as f:
        for line in f:
            if "sudo ipsec start" in line:
                break
        else: # not found, we are at the eof
            call("sudo sh -c 'echo \"sudo ipsec start\" >> /etc/network/if-pre-up.d/firewall'", shell=True)

def main():
    cmdargs = str(sys.argv)
    client_id = None
    client_psk = None

    if len(sys.argv) == 3:
        # DEPRECATED: Moving this to cloud-config.server.j2 file
        #print(textwrap.dedent("""\
        #    Syntax is: sudo python gosecure_server_install_pi.py <client1_id> "<client1_psk>"
        #    Example: sudo python gosecure_server_install_pi.py client1.d2.local "mysupersecretpsk"\n"""))
        #exit()
        client_id = str(sys.argv[1])
        client_psk = str(sys.argv[2])

    update_os()
    enable_ip_forward()
    configure_firewall()
    enable_hardware_random()
    install_strongswan()
    configure_strongswan(client_id, client_psk)
    start_strongswan()

if __name__ == "__main__":
    main()
