#!/usr/bin/env python3
# Copyright (c) 2016 Slanted Media SPRL. All rights reserved.

"""
    Tool for VLAN configuration
"""
import argparse
import paramiko
import re

USER = "pi"
PASSWORD = "raspberry"
HOST = "bvrpi.local"

class ClientSSH(object):
    def __init__(self, user, password, host):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.user = user
        self.password = password
        self.host = host
        
    def connect(self):
        self.client.connect(self.host, username=self.user, password=self.password)

    def close(self):
        self.client.close()

    def getfiles(self):
        ftp = self.client.open_sftp()
        ftp.get('/etc/network/interfaces', 'interfaces')
        ftp.get('/etc/dhcpcd.conf', 'dhcpcd.conf')
        ftp.close()

    def getvlans(self):
        _, stdout, _ = self.client.exec_command(\
            "/sbin/ifconfig -s | /usr/bin/awk 'NR>1{print $1}'")
        lines = stdout.readlines()
        vlans = []
        for (i, line) in enumerate(lines):
            lines[i] = line.rstrip()
            pattern = re.compile(r'eth\d\.(\d)')
            match = re.match(pattern, line)
            if (match):
                vlans.append(match.group(0))
        print(vlans)
                




parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--list", action="store_true")
group.add_argument("--action", choices=["add", "delete"])
args = parser.parse_args()
print(args.list)

client = ClientSSH(USER, PASSWORD, HOST)
