from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.contrib.auth.models import User
from .dbcommands import createServerInterface,createNewKey
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
        return "error"
    
    with transaction.atomic():
        key.save()
        interface.save()

    return 

def generateServerConfText(serverInterface: Interface):
    serverPeers = Peer.objects.filter(peer_key = serverInterface.interface_key)

    conf = f"""
[Interface]
PrivateKey = {serverInterface.interface_key.private_key}
ListenPort = {serverInterface.listen_port}
Address = {serverInterface.ip_address}
SaveConfig = true
""".strip()
    
    for peer in serverPeers:
        conf = conf + '\n\n'
        conf = conf + f"""
[Peer]
PublicKey = {peer.interface.interface_key.public_key}
AllowedIPs = {peer.interface.ip_address}
""".strip()

    return conf, serverInterface.name

