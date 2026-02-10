from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from .wireguard import addWGPeer,removeWGPeer
from .dbcommands import getServerInterface,createNewKey,createClientInterface,createPeer
from django.db import transaction
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('test')



def createNewClient(user : User, name : str, serverInterface : Interface = getServerInterface()):
    same = Interface.objects.filter(name = name)
    if same:
        return False
    
    try:
        key = createNewKey(user, name=name)
        interface = createClientInterface(user,key, serverInterface)
        peer = createPeer(serverInterface.interface_key,interface)
    except TypeError as e:
        return e.__str__()
    except ValueError as e:
        return e.__str__()
    except:
        return "Error with creating client"

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

def generateClientConfText(clientInterface : Interface, serverPeer : Peer,endpoint:str, listenPort:str):
    conf = f"""
[Interface]
PrivateKey = {clientInterface.interface_key.private_key}
Address = {clientInterface.ip_address}

[Peer]
PublicKey = {serverPeer.peer_key.public_key}
Endpoint = {endpoint}:{listenPort}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = {serverPeer.persistent_keepalive}
""".strip()
    
    return conf
    

def generateClientConf(key : Key):
    clientInterface = Interface.objects.get(interface_key = key)
    if (clientInterface.interface_type == Interface.SERVER):
        return "Pro server nemůže být vrácená konfigurace."
    
    serverPeer = Peer.objects.get(interface = clientInterface)
    serverInterface = getServerInterface()

    return generateClientConfText( 
        clientInterface = clientInterface,
        serverPeer = serverPeer,
        endpoint = serverInterface.server_endpoint,
        listenPort = serverInterface.listen_port)