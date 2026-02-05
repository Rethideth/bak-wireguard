from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from .wireguard import generateKeyPair,addWGPeer, genAndSaveClientConf
from django.db import transaction
from django.contrib.auth.models import User

import ipaddress

SUBNET              = "23"
START_IPADDRESSES   = "10.10.0.0"
KEEPALIVE           = 25


def allocateIpaddress():
    start = START_IPADDRESSES+'/'+SUBNET
    base = ipaddress.ip_network(start)

    occupied = Interface.objects.values_list('ip_address',flat=True)
    mappedList = set(map(ipaddress.IPv4Network,occupied))

    for ip in base.hosts():
        if ipaddress.IPv4Network(ip) not in mappedList:
            return str(ipaddress.IPv4Network(ip))

    return "error"


def createNewKey(user : User):
    privateKey, publicKey = generateKeyPair()
    newkey = Key(
        user = user,
        private_key = privateKey,
        public_key = publicKey
    )

    return newkey
    

def createClientInterface(user : User,key : Key, name : str):
    interfaceName = user.username +'-'+name
    interface = Interface(
        name = interfaceName,
        interface_key = key,
        ip_address = allocateIpaddress(),
        interface_type = Interface.CLIENT
    )

    return interface

def createClientPeer(serverKey : Key, clientInterface : Interface):
    peer = Peer(
        interface = clientInterface,
        peer_key = serverKey,
        persistent_keepalive = KEEPALIVE
    )
    return peer

def createNewClient(user : User, name : str):
    same = Interface.objects.filter(name = name)
    if same:
        return False
    
    serverInterface = Interface.objects.get(interface_type = Interface.SERVER)

    result = False

    # create new client
    key = createNewKey(user)
    interface = createClientInterface(user,key,name)
    peer = createClientPeer(serverInterface.interface_key,interface)
    
    with transaction.atomic():
        # set temporary interface for wireguard
        result = addWGPeer(
                serverInterface.name, 
                interface.interface_key.public_key,
                ipAddress=interface.ip_address)
        
        Key.save(key)
        Interface.save(interface)
        Peer.save(peer)
  
        # save config for new client 
        genAndSaveClientConf(interface,peer)
        
    return 

def deleteClient(user,key):

    pass