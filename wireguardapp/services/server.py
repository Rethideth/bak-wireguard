from wireguardapp.models import Interface, Peer, PeerSnapshot, Key,Profile
from django.contrib.auth.models import User
from .createmodel import createServerInterface,createNewKey
from wireguardapp.database.savemodel import saveServer,deleteServer,updateProfile,updateInterfaceSesssion,deleteUser,updateInterfaceEndpoint,updateInterfacePort,updateInterfaceIpaddress,updateInterfaceNetwork
from .wireguardcmd import startWGserver,stopWGserver,isWGserverUp,getWGPeersState,selectAllNetworkInterfaces,addWGPeer,removeWGPeer,saveWgDump
from wireguardapp.database.selector import selectInterfacePeers,selectOrderedPeerSnapshots,selectAllServerInterfaces,selectInterfaceFromId,selectFirstServerInterface,selectAllNonAdminUsers,selectUserFromId,selectOrCreateUserProfile,selectUserPeers,selectInterfacesFromServerInterface
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from collections import defaultdict
import ipaddress


import logging

logger = logging.getLogger('web')



def getFirstServerInterface() -> Interface:
    return selectFirstServerInterface()

def getServerInterfaceFromId(interfaceId : int) ->Interface:
    """
    Gets a server interface from its own id.

    :param interfaceId: Id of the server interface
    :type interfaceId: int

    :return: The interface of the given id
    :rtype: Interface
    """
    return selectInterfaceFromId(interfaceId)

def getServerInterfaces():
    """Returns all server interfaces. See `selector.getAllServerInterface` for more."""
    return selectAllServerInterfaces()

def createNewServer(name : str, ipNetwork : str, networkMask : str, endpoint : str, port : str):
    """
    Creates a new server for wireguard.
    Will create a new key and a interface and then save them, if there weren't any errors.
    The key of the server interface is not owned by any user.
    

    :param name: The name for the server key.
    :type name: str

    :param ipNetwork: The network of the new server interface. Has a form like `10.10.1.0` network address
        Will select first available ip address interface from the network.
    :type ipNetwork: str

    :param networkMask: The netmask of the ip network.
    :type networkMask: str

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
            netMask = networkMask,
            endpoint = endpoint,
            port = port)
    except ValueError:
        return "Hodnoty nového server rozhraní nejsou validní."
    except:
        return "Selhalo vytváření nového rozhraní serveru."
    
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
    """ 
    Tries to start the wireguard server interface service. See `wireguard.startWGserver` for more.
    Also increments session number of the server interface.
    """
    updateInterfaceSesssion(serverInterface=serverInterface)
    result = startWGserver(serverInterface, interfaceInternetName)
    saveWgDump(serverInterface)
    return result

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
    
    :param serverInterface: The interface to get all of its peer snapshots
    :type serverInterface: Interface

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

def getAllClientUsers():
    """
    Gets all users that aren not superuser of staff.

    :return: All users that have the field `is_superuser` False
    :rtype: QuerySet[User]
    """
    return selectAllNonAdminUsers()


def switchverifyProfile(userId : int) ->Profile:
    target = selectUserFromId(userId)
    profile = selectOrCreateUserProfile(target)

    if profile.verified:
        updateProfile(profile=profile,verifyState=False)
        disconnectUserFromWg(target)
    else:
        updateProfile(profile=profile,verifyState=True)
        connectUserToWg(target)

    return selectOrCreateUserProfile(target)


def connectUserToWg(user : User):
    userPeers = selectUserPeers(user)

    for peer in userPeers:
        try:
            addWGPeer(
                serverInterfaceName=peer.interface.name,
                peerKey=peer.peer_interface.interface_key.public_key,
                ipAddress=peer.peer_interface.ip_address)
        except:
            pass

def disconnectUserFromWg(user: User):
    userPeers = selectUserPeers(user)

    for peer in userPeers:
        try:
            removeWGPeer(
                serverInterfaceName=peer.interface.name,
                peerKey=peer.peer_interface.interface_key.public_key)
        except:
            pass

def removeUser(userId:int) ->str|None:
    user = selectUserFromId(userId)
    if user is None:
        return 'Uživatel nenalezen'
    disconnectUserFromWg(user=user)
    deleteUser(user=user)
    return
    


def updateServer(interface:Interface, changed = list):
    try:
        with transaction.atomic():
            if 'ip_network' in changed or 'ip_network_mask' in changed:
                updateServerPeersIpAddresses(serverInteface=interface)
            if 'server_endpoint' in changed:
                updateInterfaceEndpoint(interface=interface, endpoint=interface.server_endpoint)
            if 'listen_port' in changed:
                updateInterfacePort(interface=interface,port=interface.listen_port)
    except ValueError as e:
        return str(e)
    except:
        return 'Nastala chyba při aktualizaci serveru'



def updateServerPeersIpAddresses(serverInteface:Interface):
    network = ipaddress.ip_network(f"{serverInteface.ip_network}/{serverInteface.ip_network_mask}")
    logger.info(f"network: {network}")

    # if not enough addresses for clients
    clients = selectInterfacesFromServerInterface(serverInterface=serverInteface)
    count = network.num_addresses - 2
    if count < clients.__len__() + 1:
        raise ValueError("Velikost sítě není dostačujíčí pro všechny klienty")
    
    

    updateInterfaceNetwork(serverInteface,serverInteface.ip_network,serverInteface.ip_network_mask)
    hosts = network.hosts()
    address = next( hosts )
    updateInterfaceIpaddress(serverInteface, address)
    for client in clients:
        ip = next(hosts)
        updateInterfaceIpaddress(client,ip)

    



