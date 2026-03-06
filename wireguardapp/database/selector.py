from multiprocessing.managers import BaseManager
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key,Profile
from django.contrib.auth.models import User
from django.db.models import OuterRef, Subquery
from django.db.models import F, Window
from django.db.models.functions import RowNumber

def selectFirstServerInterface() -> Interface:
    """
    Returns the first server interface.

    :returns: Returns the server interface
    :rtype: Interface
    """
    interface = Interface.objects.filter(interface_type = Interface.SERVER).first()
    return interface

def selectAllServerInterfaces():
    """
    Returns all wireguard server interfaces that exist in database.

    :returns: Returns interfaces with interface type server
    :rtype: QuerySet[Interface] 
    """
    return Interface.objects.filter(interface_type = Interface.SERVER)


def selectClientsServerInterface(clientKey : Key) -> Interface:
    """
    Gets the server interface of the given client based on the provided key.

    :param clientKey: The key of a client. 
    :type clientKey: Key

    :return: Interface of the server. The client based on its key is connected to this server interface.
    :rtype: Interface
    """
    clientpeer = Peer.objects.get(peer_interface__interface_key = clientKey)
    return clientpeer.interface

def selectInterfaceFromId(interfaceId : int) -> Interface:
    """
    Gets the interface object from its own id.

    :param interfaceId: The id of the interface. 
    :type interfaceId: int

    :return: The interface object.
    :rtype: Interface

    """
    return Interface.objects.get(id = interfaceId)

def selectInterfaceFromKey(interfaceKey : Key) -> Interface:
    """
    Gets the interface object from its own Key object.

    :param interfaceId: The Key of the interface. 
    :type interfaceId: Key

    :return: The interface object.
    :rtype: Interface
    """
    return Interface.objects.get(interface_key = interfaceKey)

def selectUserKeys(user : User):
    """
    Returns users all keys.
    
    :param user: Specifies whose keys to get.
    :type user: User
    :returns: Returns the users keys.
    :rtype: QuerySet[Key]
    """
    return Key.objects.filter(user = user)


def selectOrderedPeerSnapshots(serverInterface : Interface):
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

def selectInterfacePeers(interface :Interface):
    """
    Returns all interface owned peers. 

    :return: List of interface peers.
    :rtype: QuerySet[Peer]
    """
    return Peer.objects.filter(interface = interface)


def selectVerifiedPeersFromServerInterface(serverInterface :Interface):
    """
    Returns all clients peers that connects to the provided `serverInterface`. 
    Returns only peers with verified users.

    :param serverInterface: The interface object to get all cliets peer.

    :return: List of clients peer that connect to the server interface.
    :rtype: QuerySet[Peer]
    """
    return Peer.objects.filter(
        interface=serverInterface,
        peer_interface__interface_key__user__profile__verified=True
        )
    
def selectInterfacesFromServerInterface(serverInterface :Interface):
    """
    Returns all clients interfaces that connects to the provided `serverInterface`. 

    :param serverInterface: The interface object to get all cliets peer.

    :return: List of clients interfaces that connect to the server interface.
    :rtype: QuerySet[Interface]
    """
    peers = Peer.objects.filter(interface = serverInterface).select_related("peer_interface")
    return [peer.peer_interface for peer in peers]
    


def selectKeyFromId(keyId :int) -> Key | None:
    """
    Returns the instance of a key based on a given id if it exists.

    :param keyId: The id of the key to return
    :type keyId: int

    :returns: Instance of a key based on the provided id or None.
    :rtype: Key | None
    """
    return Key.objects.filter(
        id=keyId,
    ).first()

def selectInterfacesFromName(name : str):
    """
    Returns all interfaces with the provided name. 

    :param name: The searched name of interfaces
    :type name: str

    :return: All interfaces with the same name
    :rtype: QuerySet[Interface]
    """
    return Interface.objects.filter(name = name)

def selectClientInterfacePeer(interface :Interface) -> Peer | None:
    """
    Returns a peer of the client interface.

    :param interface: The interface of the client
    :type interface: Interface

    :return: Peer object of the client interface. The first and maybe only peer owned by the given interface.
    :rtype: Peer | None
    """
    return Peer.objects.filter(peer_interface = interface).first()

def selectUserProfile(user : User) -> Profile:
    """
    Returns the profile of the given user.

    :param user: The user to return its own profile
    :type user: User

    :return: Profile instance of the given user
    :rtype: Profile
    """
    return Profile.objects.get(user = user)

def selectAllNonAdminUsers():
    """
    Returns all users that arent superusers.

    :return: All user that have the field `is_superuser` False
    :rtype: QuerySet[User]
    """
    return User.objects.exclude(is_superuser=True)

def selectUserFromId(id : int) -> User | None:
    """
    Returns a user based on it own id/pk.

    :param id: The id of the seached user.
    :type id: int

    :return: The user of the given id if it is exists.
    :rtype: User | None
    """
    return User.objects.filter(pk=id).first()

def selectUserPeers(user : User):
    """
    Returns the peers that the given user (and its own keys) uses.

    :param user: The user to return the peers that are connected to this user.
    :type user: User 

    :return: The peers that are connected to the user
    :rtype: QuerySet[Peer]
    """
    return Peer.objects.filter(peer_interface__interface_key__user = user)

def selectUserKeys(user:User):
    """
    Returns all keys that the given user owns.
    
    :param user: The user to returns its own keys.
    :type user: User

    :return: All keys that the given user owns.
    :rtype: QuerySet[Key]
    """
    return Key.objects.filter(user = user)