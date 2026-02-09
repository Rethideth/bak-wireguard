from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from .wireguard import generateKeyPair,addWGPeer,removeWGPeer
from .server import allocateIpaddress,getServerInterface
from django.db import transaction
from django.contrib.auth.models import User

import ipaddress

KEEPALIVE           = 25


def createNewKey(user : User):
    privateKey, publicKey = generateKeyPair()
    newkey = Key(
        user = user,
        private_key = privateKey,
        public_key = publicKey
    )

    return newkey
    

def createInterface(user : User,key : Key, name : str):
    if user.is_superuser:
        interfacetype = Interface.SERVER
    else:
        interfacetype = Interface.CLIENT
    interfaceName = user.username +'-'+name
    interface = Interface(
        name = interfaceName,
        interface_key = key,
        ip_address = allocateIpaddress(),
        interface_type = interface
    )

    return interface

def createPeer(serverKey : Key, clientInterface : Interface):
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
    
    serverInterface = getServerInterface()

    result = False

    # create new client
    key = createNewKey(user)
    interface = createInterface(user,key,name)
    peer = createPeer(serverInterface.interface_key,interface)
    
    try:
        with transaction.atomic():
            # set temporary interface for wireguard
            result = addWGPeer(
                    serverInterface.name, 
                    interface.interface_key.public_key,
                    ipAddress=interface.ip_address)
            
            Key.save(key)
            Interface.save(interface)
            Peer.save(peer)
    

    except RuntimeError as e:
        return e.__str__()
        
    return 

def deleteClient(user : User, key : Key):
    serverInterface = getServerInterface()

    try:
        with transaction.atomic():
            result = removeWGPeer(
                serverInterfaceName =   serverInterface.name,
                peerKey =               key.public_key
            )
            key.delete()
    except RuntimeError as e:
        return e.__str__()
        
    return 