from wireguardapp.models import Interface, Peer,PeerSnapshot, Key
from .wireguard import addWGPeer,removeWGPeer,generateClientConfText
from .dbcommands import createNewKey,createClientInterface,createClientServerPeers
from .selector import getServerInterface
from django.db import transaction
from django.contrib.auth.models import User
import logging
import ipaddress

logger = logging.getLogger('test')


def createNewClient(user : User, name : str, serverInterface : Interface = getServerInterface()):
    """
    Creates a new client for the wireguard server. 
    Client need a Key, its Interface and Peer for client and server interface for connection.
    Saving objects is atomic.
    Also it will enable wireguard connection for this client immediately.
    
    :param user: The user that is the client. Is used to create users private and public key.
    :type user: User
    :param name: Name for the users key.
        User will identify this connection based on this name (e.g. 'My key for my notebook')
    :type name: str
    :param serverInterface: The server interface that the client will connect to for VPN access.
        Will use the interface with server type. Use getServerInterface() to get existing server Interface.
    :type serverInterface: Interface
    :return: An error message if something went wrong in a form of string. None if no error happened.
        TypeError if the serverInterface parameter does not have a interface_type = 'server'.
        ValueError if the serverInterface ip network does not have unoccupied ip addresses.
        RunTimeError if adding a wireguard peer failed using a privileged script. Usually server interface is down.
    :rtype: str | None
    """
    same = Interface.objects.filter(name = name)
    if same:
        return False
    
    try:
        key = createNewKey(user, name=name)
        interface = createClientInterface(user,key, serverInterface)
        clientPeer, serverPeer = createClientServerPeers(serverInterface,interface)
    except TypeError as e:
        return e.__str__()
    except ValueError as e:
        return e.__str__()
    except:
        return "Error with creating client"

    try:
        with transaction.atomic():
            # set temporary interface for wireguard
            result = addWGPeer(
                    serverInterface.name, 
                    interface.interface_key.public_key,
                    ipAddress=interface.ip_address)
            
            Key.save(key)
            Interface.save(interface)
            Peer.save(clientPeer)
            Peer.save(serverPeer)
    

    except RuntimeError as e:
        return e.__str__()
        
    return 

def deleteClient(user : User, key : Key):
    """
    Deletes a client with its own key. The deleted key will cascade to its own interface and peer.
    Removes the connection from Wireguard.
    
    :param user: User for this client.
    :type user: User
    :param key: The Key for deletion
    :type key: Key
    :return: An error message if something went wrong, None if no error happened.
        RunTimeError if removing a wireguard peer failed using a privileged script. Usually server interface is down.
    :rtype: str | None
    """
    serverInterface = getServerInterface()

    try:
        with transaction.atomic():
            result = removeWGPeer(
                serverInterfaceName =   serverInterface.name,
                peerKey =               key.public_key
            )
            key.delete()
    except RuntimeError as e:
        return e.__str__()
        
    return 



def generateClientConf(key : Key, onlyVpn : bool = False) -> str:
    """
    Return a string text for a wireguard configuration file for clients. 
    Has a full or split tunnel for configuration.
    Uses given key for the client.
    If given the server interface, will return only 'Pro server nemůže být vrácená konfigurace.'
    
    :param key: The identification for selecting which client will have the configuration text.
        Key must have a client interface.
    :type key: Key
    :param onlyVpn: Select if the connection will be 
        full tunel (All network communication will go through VPN) 
        or split tunel (Network communication will go only through VPN if to communicate with the private network of the VPN)
    :type onlyVpn: bool
    :return: Configuration text for wireguard ready for copying or an error message for server interface.
    :rtype: str
    """
    clientInterface = Interface.objects.get(interface_key = key)
    if (clientInterface.interface_type == Interface.SERVER):
        return "Pro server nemůže být vrácená konfigurace."
    
    serverPeer = Peer.objects.get(interface = clientInterface)
    serverInterface = getServerInterface()

    if (onlyVpn):
        return generateClientConfText( 
        clientInterface = clientInterface,
        serverPeer = serverPeer,
        endpoint = serverInterface.server_endpoint,
        listenPort = serverInterface.listen_port,
        allowedIPs = ipaddress.IPv4Interface(serverInterface.ip_address).network)
    else:
        return generateClientConfText( 
            clientInterface = clientInterface,
            serverPeer = serverPeer,
            endpoint = serverInterface.server_endpoint,
            listenPort = serverInterface.listen_port)