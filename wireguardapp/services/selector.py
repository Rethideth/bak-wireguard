from multiprocessing.managers import BaseManager
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery

def getServerInterface() -> Interface:
    """
    Returns the server interface.
    """
    interface = Interface.objects.get(interface_type = Interface.SERVER)
    return interface

def getUserKeys(user : User):
    return Key.objects.filter(user = user)

def getServerPeerSnapshots():
    snapshots = PeerSnapshot.objects.filter(
        peer__interface=getServerInterface()
    ).order_by("peer__interface__name", "peer__peer_key", "-collected_at")
    return snapshots
    
def getLatestPeerSnapshots():
    latest_snapshot = PeerSnapshot.objects.filter(
        peer=OuterRef('peer'), peer__interface=getServerInterface()
    ).order_by('-collected_at')

    queryset = PeerSnapshot.objects.filter(
        collected_at=Subquery(
            latest_snapshot.values('collected_at')[:1]
        )
    )
    return queryset

def getServerPeers(interface : Interface):
    return Peer.objects.filter(peer_key = interface.interface_key)