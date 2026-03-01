from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from .createmodel import createServerInterface,createNewKey
from wireguardapp.database.savemodel import saveServer,deleteServer
from .wireguard import startWGserver,stopWGserver,isWGserverUp,getWGPeersState,selectAllNetworkInterfaces
from wireguardapp.database.selector import selectInterfacePeers,selectOrderedPeerSnapshots,selectAllServerInterfaces,selectInterfaceFromId,selectFirstServerInterface
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from collections import defaultdict
import ipaddress


import logging

logger = logging.getLogger('test')



def getFirstServerInterface() -> Interface:
    return selectFirstServerInterface()

def getServerInterfaceFromId(interfaceId : int):
    return selectInterfaceFromId(interfaceId)

def getServerInterfaces():
    """Returns all server interfaces. See `selector.getAllServerInterface` for more."""
    return selectAllServerInterfaces()

def createNewServer(name : str, ipNetwork : str, endpoint : str, port : str):
    """
    Creates a new server for wireguard.
    Will create a new key and a interface and then save them, if there weren't any errors.
    The key of the server interface is not owned by any user.
    

    :param name: The name for the server key.
    :type name: str

    :param ipNetwork: The network of the new server interface. Has a form like `10.10.1.0/24` network address/mask
        Will select first available ip address interface from the network.
    :type ipNetwork: str

    :param endpoint: The public address of the wireguard VPN server. Port will be only 51820.
    :type endpoint: str

    :param port: Port of the wireguard server interface.
    :type port: str

    :return: None if executed without errors, string for a message what kind of error happened to send back to the web page form.
    :rtype: None | str
    """
    try:
        key = createNewKey(None,name)
        interface = createServerInterface(
            key = key,
            ipNetwork = ipNetwork,
            endpoint = endpoint,
            port = port)
    except ValueError:
        return "Hodnoty nového server interface nejsou validní."
    except:
        return "Selhalo vytváření nového interface serveru."
    
    saveServer(key,interface)

    return 

def removeServer(serverInterface : Interface):
    """
    Removes the server by the given interface.
    It will try to stop the server wireguard interface first, then deletes the server key.
    The deleted key will cascade to its interface.

    :param serverInterface: The server interface to be deleted
    :type serverInterface: Interface
    """
    stopServer(serverInterface)
    deleteServer(serverInterface.interface_key)

def startServer(serverInterface : Interface, interfaceInternetName : str):
    """ Tries to start the wireguard server interface service. See `wireguard.startWGserver` for more."""
    return startWGserver(serverInterface, interfaceInternetName)

def stopServer(serverInterface : Interface):
    """ Tries to stop the wireguard server interface service. See `wireguard.stopWGserver` for more."""
    return stopWGserver(serverInterface)

def checkServer(serverInterface : Interface):
    """ Checks if the server interface is running or stopped. See `wireguard.isWGserverUp` for more."""
    return isWGserverUp(serverInterface)


def getServerInterfacePeers(serverInterface : Interface):
    """
    Gets the peers of the `serverInterface`.

    :param serverInterface: The interface to return its own peer objects.
    :type serverInterface: Interface

    :return: The peers of the given interface.
    :rtype: QuerySet[Peer]
    """
    serverPeers = selectInterfacePeers(interface = serverInterface)
    return serverPeers

def getLastDayDiffSnapshot(serverInterface : Interface) -> list[dict]:
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
    ranked = selectOrderedPeerSnapshots(serverInterface).filter(row_number__lte=2)

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

def getWGPeerConnectionState(serverInterface : Interface):
    """
    Wrapper of the `getWGPeerState` function.

    This function accesses the wireguard service for the `getWGPeersState` function.
    """
    return getWGPeersState(serverInterface)

def getNetworkInterfaces():
    """Gets the list of all available network interfaces. See `selectAllNetworkInterfaces` for more."""
    return selectAllNetworkInterfaces()


def getInterfacePeersTotalBytes(serverInterface : Interface):
    """
    Gets all peers of the given interface and their total recieved/sent bytes.
    
    :return: Returns a list of data in a dictionary about the peer, its endpoint, recieved/sent bytes total.
    :rtype: list[dict]

    ::

        [
            {
                "peer": Peer,       # Peer object of the Snapshot
                "endpoint": str,    # Endpoint of the Peer
                "rx_total": int,    # Total recieved bytes through this interface for this peer
                "tx_total": int,    # Total sent bytes through this interface for this peer
            },
        ]

    """
    peers = getServerInterfacePeers(serverInterface)
    ranked = selectOrderedPeerSnapshots(serverInterface=serverInterface)

    endpoints = defaultdict(set)

    for snapshot in ranked:
        endpoints[snapshot.peer].add(snapshot.endpoint)

    table = []

    for peer in peers:
        table.append({
                "peer": peer,
                "endpoint": endpoints[peer],
                "rx_total": peer.total_rx_bytes,
                "tx_total": peer.total_tx_bytes,
            })
    return table
