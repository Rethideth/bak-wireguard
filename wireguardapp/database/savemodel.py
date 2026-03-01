from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction


def saveClient(clientKey : Key, clientInterface : Interface, clientPeer : Peer, serverPeer: Peer):
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
        Peer.save(clientPeer)
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
    serverKey.delete()