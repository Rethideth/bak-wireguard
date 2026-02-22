from unittest import TestCase
from django.contrib.auth import get_user_model
from wireguardapp.services.dbcommands import createNewKey
from .models import Interface,Peer, Key
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
    
    def testKey(self):
        key = createNewKey(None, "baf")
        print(key)
        key.save()
        return True
    
    def testname(self):
        names = ["wg-server1",'wg-server2','wg-server4']
        names2 = []
        nums = [int(re.search(r'\d+',x).group()) for x in names]
        num = max(nums,default=-1)
        
        print(num+1)

        return True

