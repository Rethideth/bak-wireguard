from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.contrib.auth.models import User

import ipaddress

def getServerInterface():
    return Interface.objects.get(interface_type = Interface.SERVER)

def allocateIpaddress():
    serverInterface = getServerInterface()
    interface = ipaddress.ip_interface(serverInterface.ip_address)
    base = interface.network

    clientInterfaces = Interface.objects.filter(interface_type = Interface.CLIENT).values_list('ip_address',flat=True)
    occupied = {ipaddress.IPv4Interface(i).ip for i in clientInterfaces}
    occupied.add(interface.ip)

    for ip in base.hosts():
        if ip not in occupied:
            return f'{ip}/32'

    raise ValueError

def createNewServer():
    pass
