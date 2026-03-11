from wireguardapp.models import Interface, Peer, PeerSnapshot, Key, Profile
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber


def saveClient(clientKey : Key, clientInterface : Interface, serverPeer: Peer):
    """
    Saving of client objects (Key, Interface, client and server peers) in a atomic transaction.

    :param clientKey: Instance of a Key model of the client to save to database.
    :type clientKey: Key

    :param clientInterface: Instance of a Interface model of the client to save to database.
    :type clientInterface: Interface

    :param clientPeer: Instance of a Peer model of a client interface, 
        that has the public key of a server interface to save to database.
    :type clientPeer: Peer

    :param serverPeer: Instance of a Peer model of a server interface, 
        that has the public key of a client interface to save to database.
    :type serverPeer:

    """
    with transaction.atomic():
        Key.save(clientKey)
        Interface.save(clientInterface)
        Peer.save(serverPeer)
    return


def saveServer(serverKey : Key, serverInterface : Interface):
    with transaction.atomic():
        Key.save(serverKey)
        Interface.save(serverInterface)

def deleteClient(clientKey : Key):
    """
    Delete the client and its models from the database.
    The deleted key will cascade to its interface and peer.

    :param clientKey: The key of the client to delete clients models.
    :type clientKey: Key
    """
    clientKey.delete()

def saveKeyName(key : Key, name : str):
    """
    Changes the key name to the given name.

    :param key: The key to change the name of.
    :type key: Key

    :param name: The given name to change the key name.
    :type name: str
    """
    key.name = name
    key.save(update_fields=['name'])

def deleteServer(serverKey: Key):
    """
    Deletes the given server key of a server interface. 
    The deleted Key will cascade to its interface.

    :param serverKey: The key of the server interface
    :type serverKey: Key
    """
    serverKey.delete()

def saveUser(user : User,profile : Profile):
    """
    Saves the instances of user with its own profile.

    :param user: The instance of the user to be saved
    :type user: User

    :param profile: The instance of the profile of a user to be saved
    :type profile: Profile
    """
    user.save()
    profile.save()

def updateProfile(profile : Profile,verifyState : bool = None, keyLimit : int = None,keyCount : int = None ):
    """
    Updates fileds of the given profile based on the given parameter `verifyState`, `keyLimit`,`keyCount`.
    If a parameter of the field is None (default is None), it wont be updated.

    :param profile: The profile to be updated. Based on the other given parameters, 
        those fields of the profile instance will be changed. 
    :type profile: Profile

    :param verifyState: The field `verified` of the profile instance.
    :type verifyState: bool | None

    :param keyLimit: The field `key_limit` of the profile instance.
    :type keyLimit: int | None

    :param keyCount: The field `key_count` of the profie instance.
    :type keyCount: int | None
    """
    fields = []

    if verifyState is not None:
        profile.verified = verifyState
        fields.append('verified')  

    if keyLimit is not None:
        profile.key_limit = keyLimit  
        fields.append('key_limit')

    if keyCount is not None:
        profile.key_count = keyCount  
        fields.append('key_count')

    if fields:
        profile.save(update_fields=fields)
    
def updateInterfaceSesssion(serverInterface : Interface):
    """
    Increments the given interface session. Session is used for logging state of the interface network transmit.
    The numberic field `session_number` of the interface instance will be increased be 1 and then saved.

    :param serverInterface: The interface to increment its own `session_number`.
    :type serverInterface: Interface
    """
    serverInterface.session_number += 1
    serverInterface.save(update_fields=['session_number'])

def deleteUser(user:User):
    """
    Deleted the given user.

    :param user: The user to delete to.
    :type user: User
    """
    User.delete(user)


def updateInterfaceEndpoint(interface :Interface, endpoint : str):
    """
    Changes the `server_endpoint` of the given interface.

    :param interface: The interface to change the field.
    :type interface: Interface

    :param endpoint: The endpoint to change
    :type endpoint: str
    """
    interface.server_endpoint = endpoint
    interface.save(update_fields=['server_endpoint'])

def updateInterfacePort(interface : Interface, port : int):
    """
    Changes the `listen_port` of the given interface.

    :param interface: The interface to change the field.
    :type interface: Interface

    :param port: The port to change.
    :type port: int
    """
    interface.listen_port = port
    interface.save(update_fields=['listen_port'])

def updateInterfaceIpaddress(interface : Interface, ipaddress : str):
    """
    Changes the `ip_address` of the given interface.

    :param interface: The interface to change the field.
    :type interface: Interface

    :param ipaddress: The ipaddress to change
    :type ipaddress: str
    """
    interface.ip_address = ipaddress
    interface.save(update_fields=['ip_address'])

def updateInterfaceNetwork(interface :Interface, ipnetwork :str, mask :str):
    interface.ip_network = ipnetwork
    interface.ip_network_mask = mask
    interface.save(update_fields=['ip_network','ip_network_mask'])