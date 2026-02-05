from unittest import TestCase
from django.contrib.auth import get_user_model
from .models import Interface,Peer, Key
import ipaddress
import os
import subprocess
# Create your tests here.

SUBNET              = "23"
START_IPADDRESSES   = "10.10.0.0"

class TestSyntax(TestCase):
    def test_conf(self):
        list = {"10.10.0.1/32", "10.10.0.2/32","10.10.0.3/32"}
        start = START_IPADDRESSES+'/'+SUBNET
        base = ipaddress.ip_network(start)

        mappedList = set(map(ipaddress.IPv4Network,list))

        for ip in base.hosts():
            if ip not in mappedList:
                return str(ipaddress.IPv4Network(ip))
        return False
    

class TestSubprocess(TestCase):
    def workingCommand(self):
        serverInterfaceName = 'wg-server'
        peerKey = 'B5L3cSXODu237hSD6uIBlV5lFHJxUw0wMqMM/X53CwQ='
        ipAddress = '10.10.0.10/32'
        try:
            result = subprocess.run(
                [
                    "/var/www/bakproject/scripts/enablepeer.sh", 
                    serverInterfaceName, peerKey,ipAddress
                ],
                check=True,

            )
        except subprocess.CalledProcessError as e:
            print("Cannot add a new peer")
            print("stderr:", e.stderr)
            raise ZeroDivisionError
        except PermissionError:
            print("Permission denied")
            raise ZeroDivisionError

        raise NameError