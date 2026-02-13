from multiprocessing.managers import BaseManager
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from django.db.models.functions import RowNumber

def getServerInterface() -> Interface:
    """
    Returns the server interface.

    :returns: Returns the server interface
    :rtype: Interface
    """
    interface = Interface.objects.get(interface_type = Interface.SERVER)
    return interface

def getUserKeys(user : User):
    """
    Returns users all keys.
    
    :param user: Specifies whose keys to get.
    :type user: User
    :returns: Returns the users keys.
    :rtype: QuerySet[Key]
    """
    return Key.objects.filter(user = user)

def getServerPeerSnapshots():
    """
    Returns a list of snapshots ordered by interfaces (asc), peers (asc) and date of collected snapshots(desc).
    Only gets server peers.

    :return: List of snapshots ordered.
    :rtype: QuerySet[Snapshots]
    """
    snapshots = PeerSnapshot.objects.filter(
        peer__interface=getServerInterface()
    ).order_by("peer__interface__name", "peer__peer_key", "-collected_at")
    return snapshots
    
def getOrderedPeerSnapshots():
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
    ).filter(peer__interface = getServerInterface())
    return ranked

def getInterfacePeers(interface :Interface):
    """
    Returns all interface peers. 

    :return: List of interface peers.
    :rtype: QuerySet[Peer]
    """
    return Peer.objects.filter(interface = interface)