from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from .dbcommands import createServerInterface,createNewKey
from .wireguard import startWGserver,stopWGserver,isWGserverUp,getWGPeersState
from .selector import getServerInterface,getInterfacePeers,getOrderedPeerSnapshots,getServerPeerSnapshots
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from collections import defaultdict
import ipaddress


import logging

logger = logging.getLogger('test')

def createNewServer(user : User, name : str, ipinterface :str, endpoint:str):
    """
    Creates a new server for wireguard. There will be only one server interface. 
    Will create a new key and a interface and then save them, if there weren't any errors.
    
    :param user: The user who has the server key.
    :type user: User

    :param name: The name for the server key.
    :type name: str

    :param ipinterface: The private network ip address for the server interface.
        Specifies the ip address and the network of the interface. 
        E.g 10.10.0.2/24 -> ip address of the interface will be 10.10.0.2
        and the network of the interface is 10.10.0.0/24
    :type ipinterface: str

    :param endpoint: The public address of the wireguard VPN server. Port will be only 51820.
    :type endpoint: str


    :return: None if executed without errors, string for a message what kind of error happened to send back to the web page form.
    :rtype: None | str
    """
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
    """ Tries to start the wireguard server interface service."""
    return startWGserver()

def stopServer():
    """ Tries to stop the wireguard server interface service."""
    return stopWGserver()

def checkServer():
    """ Checks if the server interface is running or stopped. 
    :return: True for running and False for stopped server interface.
    :rtype: bool
    """
    return isWGserverUp()


def getServerInterfaceWithPeers():
    """
    Gets the server interface and its own peers returned in a tuple.

    :return: Tuple of the server interface and its own peers.
    :rtype: tuple[Interface, QuerySet[Peer]]
    """
    interface = getServerInterface()
    serverPeers = getInterfacePeers(interface = interface)
    return interface, serverPeers

def getServerPeersSnapshots():
    """ Gets all server peer snapshots ordered by peer (ascending) and collected_at date (descending). """
    return getServerPeerSnapshots()

def getLastDayDiffSnapshot() -> list[dict]:
    """
    Gets a Snapshot of each server Peer and their bytes recieved/sent difference of the latest snapshot and second latest snapshot.
    
    :return: Returns a list of data in a dictionary about the peer, its endpoint, recieved/sent bytes difference.
    :rtype: list[dict]

    ::

        [
            {
                "peer": Peer,       # Peer object of the Snapshot
                "endpoint": str,    # Endpoint of the Peer
                "rx_growth": int,   # Difference between last and second last snapshot of recieved bytes
                "tx_growth": int,   # Difference between last and second last snapshot of sent bytes
            },
        ]

    """
    ranked = getOrderedPeerSnapshots().filter(row_number__lte=2)

    grouped = defaultdict(list)

    for snapshot in ranked:
        grouped[snapshot.peer].append(snapshot)

    table = []

    for peer, snaps in grouped.items():
        if len(snaps) == 2:
            latest, second = snaps

            table.append({
                "peer": latest.peer,
                "endpoint": latest.endpoint,
                "rx_growth": int(latest.rx_bytes) - int(second.rx_bytes),
                "tx_growth": int(latest.tx_bytes) - int(second.tx_bytes),
            })

    return table

def getWGPeerConnectionState():
    """
    Wrapper of the `getWGPeerState` function

    This function accesses the wireguard service for the `getWGPeersState` function.
    """
    return getWGPeersState()