from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.contrib.auth.models import User
from .dbcommands import createServerInterface,createNewKey
from .wireguard import startWGserver,stopWGserver,isWGserverUp
from django.db import transaction
import ipaddress

import logging

logger = logging.getLogger('test')

def createNewServer(user : User, name : str, ipinterface :str, endpoint:str):
    if Interface.objects.filter(interface_type = Interface.SERVER).count() > 0:
        return 'Může existovat jenom jeden server interface.'
    try:
        key = createNewKey(user,name)
        interface = createServerInterface(
            key = key,
            ipinterface = ipinterface,
            endpoint = endpoint)
    except:
        return "Nemohlo se vytvořit klíč a interface pro server-"
    
    with transaction.atomic():
        key.save()
        interface.save()

    return 

def startServer():
    return startWGserver()

def stopServer():
    return stopWGserver()

def checkServer():
    return isWGserverUp()


