from multiprocessing.managers import BaseManager
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.shortcuts import get_object_or_404

def getAllServerInterfaces():
    """
    Returns all wireguard server interfaces that exist in database.

    :returns: Returns interfaces with interface type server
    :rtype: QuerySet[Interface] 
    """
    return Interface.objects.filter(interface_type = Interface.SERVER)


def getClientsServerInterface(clientKey : Key):
    clientpeer = Peer.objects.get(interface__interface_key = clientKey)
    return Interface.objects.get(interface_key = clientpeer.peer_key)


def getUserKeys(user : User):
    """
    Returns users all keys.
    
    :param user: Specifies whose keys to get.
    :type user: User
    :returns: Returns the users keys.
    :rtype: QuerySet[Key]
    """
    return Key.objects.filter(user = user)

def getServerPeerSnapshots(serverInterface : Interface):
    """
    Returns a list of snapshots ordered by interfaces (asc), peers (asc) and date of collected snapshots(desc).
    Only gets server peers.

    :return: List of snapshots ordered.
    :rtype: QuerySet[Snapshots]
    """
    snapshots = PeerSnapshot.objects.filter(
        peer__interface=serverInterface
    ).order_by("peer__interface__name", "peer__peer_key", "-collected_at")
    return snapshots
    
def getOrderedPeerSnapshots(serverInterface : Interface):
    """
    Returns a list of snapshots grouped by server peers and ordered by collected_at date of the server interface.

    :return: List of snapshots grouped by peers and ordered by collected_at date.
    :rtype: QuerySet[Snapshots]
    """
    ranked = PeerSnapshot.objects.annotate(
        row_number=Window(
            expression=RowNumber(),
            partition_by=[F('peer')],
            order_by=F('collected_at').desc()
        )
    ).filter(peer__interface = serverInterface)
    return ranked

def getInterfacePeers(interface :Interface):
    """
    Returns all interface peers. 

    :return: List of interface peers.
    :rtype: QuerySet[Peer]
    """
    return Peer.objects.filter(interface = interface)

def getKeyFromId(idKey :int) -> Key:
    """
    Gets the instance of a key based on a given id if it exists.

    :param idKey: The id of the key to return
    :type idKey: int

    :returns: Instance of a key based on the provided id.
    :rtype: Key

    :raises DoesNotExist: If the searched key does not exists.
    """
    return Key.objects.get(
        id=idKey,
    )
