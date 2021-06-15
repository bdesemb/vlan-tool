#!/usr/bin/env python3
# Copyright (c) 2016 Slanted Media SPRL. All rights reserved.

"""
    Tool for VLAN configuration
"""
import re
import paramiko

USER = "pi"
PASSWORD = "raspberry"
SUDO_PASS = PASSWORD
HOST = "bvrpi.local"

class ClientSSH(object):
    "Class to handle connection and interaction to the remote"
    def __init__(self, user, password, host):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.user = user
        self.password = password
        self.host = host

    def connect(self):
        "Establish connection"
        self.client.connect(self.host, username=self.user, password=self.password)

    def close(self):
        "Close the connection to the remote."
        self.client.close()

    def pushfiles(self):
        "Push modified files"
        ftp = self.client.open_sftp()
        ftp.put('interfaces', '/etc/network/interfaces')
        ftp.put('dhcpcd.conf', '/etc/dhcpcd.conf')
        ftp.close()

    def getvlans(self):
        "Get already configured vlan"
        _, stdout, _ = self.client.exec_command(\
            "/sbin/ifconfig -s | /usr/bin/awk 'NR>1{print $1}'")
        lines = stdout.readlines()
        vlans = []
        for (i, line) in enumerate(lines):
            lines[i] = line.rstrip()
            p = re.compile(r'eth\d\.(\d+)')
            m = p.match(line)
            if m:
                vlans.append(int(m.group(1)))
        return vlans

    def rebootRemote(self):
        "Reboot remote host"
        self.client.exec_command('/sbin/reboot now')

    def checkvlanmodule(self):
        """Check if vlan module is loaded (must be root)"""
        stdin, stdout, _ = self.client.exec_command(\
        'if /usr/bin/sudo /sbin/modinfo 8021q > /dev/null 2> /dev/null;'
        'then echo 1; else echo 0;fi', timeout=3)
        stdin.write(SUDO_PASS + '\n')
        stdin.flush()
        if stdout.readlines()[0].rstrip() == "0":
            self.client.exec_command('/usr/bin/sudo /usr/bin/apt-get install vlan &&'
                                     '/usr/bin/sudo modprobe 8021q')
            self.client.exec_command("/usr/bin/sudo /bin/su -c 'echo \"8021q\" >> /etc/modules'")

    def addvlan(self, ids):
        """ids must be an array"""
        readinter = open('interfaces', 'r')
        readdhcp = open('dhcpcd.conf', 'r')
        ilines = readinter.readlines()
        dlines = readdhcp.readlines()
        readinter.close()
        readdhcp.close()

        writeinter = open('interfaces', 'w')
        writedhcp = open('dhcpcd.conf', 'w')

        pattern = re.compile(r'#.*BVAutoConfiguration.*')

        #Delete vlan config in interfaces file
        delCountIn = 6
        markedLine = False
        for line in ilines:
            res = pattern.match(line)
            if res is None and not markedLine:
                writeinter.write(line)
            elif delCountIn == 0:
                delCountIn = 6
                markedLine = False
            elif markedLine:
                delCountIn -= 1
            else:
                markedLine = True
                delCountIn -= 1

        #Delete vlan config in dhcpch.conf file
        delCountDhcp = 6
        markedLine = False
        for line in dlines:
            res = pattern.match(line)
            if res is None and not markedLine:
                writedhcp.write(line)
            elif delCountDhcp == 0:
                delCountDhcp = 4
                markedLine = False
            elif markedLine:
                delCountDhcp -= 1
            else:
                markedLine = True
                delCountDhcp -= 1

        writeinter.close()
        writedhcp.close()

        appendinter = open('interfaces', 'a')
        appenddhcp = open('dhcpcd.conf', 'a')
        appendinter.write('\n')
        appenddhcp.write('\n')

        #Add vlans in interfaces and dhcpcd.conf
        for vid in ids:
            istr = ("# BVAutoConfiguration vlan {0}\n"
                    "auto eth0.{0}\n"
                    "iface eth0.{0} inet static\n"
                    "\taddress 192.168.178.222/23\n"
                    "\tdns-nameservers 8.8.8.8 8.8.4.4\n\n").format(vid)
            appendinter.write(istr)
            dstr = ("# BVAutoConfiguration vlan {0}\n"
                    "interface eth0.{0}\n"
                    "static ip_address=192.168.178.222/23\n"
                    "static routers=192.168.178.1\n"
                    "static domain_name_servers=192.168.178.1\n\n").format(vid)
            appenddhcp.write(dstr)

            self.client.exec_command('/usr/bin/sudo /sbin/vconfig add eth0 ' + str(vid))

        appendinter.close()
        appenddhcp.close()


#------- START -----
client = ClientSSH(USER, PASSWORD, HOST)
client.connect()
print("Connected. Please wait...", flush=True)
client.checkvlanmodule()

vs = client.getvlans()
print("Current running vlans are:", vs)

print("Which VLAN id do you want to add?")
new_id = input()
vs.append(new_id)

client.addvlan(vs)
client.pushfiles()
client.rebootRemote()

#------- END ------
client.close()
