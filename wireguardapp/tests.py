from unittest import TestCase
from django.contrib.auth import get_user_model
from .models import Interface,Peer, Key
from services.clientservice import ClientService
from services.modelfactory import ModelFactory
import ipaddress
import os
import subprocess
import re
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
    
    def testname(self):
        ModelFactory.makeServerNewName()

        return True
    
    def testnetstat(self):
        args = ["netstat", "-i"]
        result = subprocess.run(
            args=args,
            capture_output=True,
            text=True)
        
        lines = result.stdout.strip().split('\n')

        for i in range(2,len(lines),1):
            line = lines[i].split(' ')
            print(line[0])

        return False
   
    def testinvert(self):
        test = False
        print(test)
        test = not test
        print(test)
        test = not test
        print(test)
        test = not test
        print(test)

