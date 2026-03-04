from wireguardapp.models import Interface, Peer,PeerSnapshot, Key,Profile
from .wireguard import addWGPeer,removeWGPeer,generateClientConfText
from .createmodel import createNewKey,createClientInterface,createServerPeer,createProfile
from wireguardapp.database.savemodel import saveClient,deleteClient,saveUser,updateProfile
from wireguardapp.database.selector import selectClientsServerInterface,selectKeyFromId,selectInterfacesFromName,selectInterfaceFromKey,selectUserProfile,selectClientInterfacePeer,selectUserKeys
from wireguardapp.forms import CustomUserCreationForm
from django.db import transaction
from django.contrib.auth.models import User

import logging
import ipaddress

logger = logging.getLogger('wg')

def getKeyById(keyId :int)-> Key:
    """
    Tries to get Key object instance from its id if it exists. 

    :param keyId: The id of the searched Key object
    :type keyId: int

    :return: Key object instance with the same provided id.
    :rtype: Key
    """
    return selectKeyFromId(keyId=keyId)

def getClientsServerInterface(clientKey : Key) ->Interface:
    """Wrapper of `selectClientsServerInterface`. See it for more information"""
    return selectClientsServerInterface(clientKey=clientKey)

def createNewClient(user : User, name : str, serverInterface : Interface):
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
    profile = getUserProfile(user=user) 
    if not profile.verified:
        return 'Nejste ověření pro vytváření klíčů, kontaktujte správce pro ověření.'
    if profile.key_limit <= profile.key_count:
        return 'Dosáhli jste maximum počet klíču, co můžete mít.'
    

    try:
        key = createNewKey(user, name=name)
        interface = createClientInterface(user,key, serverInterface)
        serverPeer = createServerPeer(serverInterface,interface)
    except TypeError as e:
        return 'Interface pro alokaci ip adresy není typu server.'
    except ValueError as e:
        return 'Volné ip adresy pro tento interface byly vyčerpány.'
    except:
        return "Nastala chyba při vytváření klienta."

    saveClient(
        clientKey=key,
        clientInterface=interface,
        serverPeer=serverPeer)
    
    updateProfile(
        profile=profile,
        keyCount=profile.key_count+1)

    try:  # set temporary interface for wireguard  
        result = addWGPeer(
                serverInterface.name, 
                interface.interface_key.public_key,
                ipAddress=interface.ip_address)
    except RuntimeError as e:
        pass
    

    
    return 

def removeClient(user : User, key : Key):
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
    profile = getUserProfile(user=user) 
    if not profile.verified:
        return 'Nejste ověřeni, kontaktujte správce pro ověření'
    serverInterface = selectClientsServerInterface(key)

    deleteClient(clientKey=key)


    updateProfile(
        profile=profile,
        keyCount=profile.key_count-1)

    try:
        result = removeWGPeer(
            serverInterfaceName =   serverInterface.name,
            peerKey =               key.public_key
        )
            
    except RuntimeError as e:
        pass


        
    return 


def generateClientConf(user:User,key : Key, onlyVpn : bool = False) -> str:
    """
    Return a string text for a wireguard configuration file for clients. 
    Has a full or split tunnel for configuration.
    Uses given key for the client.
    If given the server interface, will return only 'Pro server nemůže být vrácená konfigurace.'
    
    :param key: The identification for selecting which client will have the configuration text.
        Key must have a client interface.
    :type key: Key
    :param onlyVpn: Select if the connection will be 

        Full tunel (False) - All network communication will go through VPN 

        Split tunel (True) - Network communication will go only through VPN to communicate with the private network of the VPN
    :type onlyVpn: bool
    :return: Configuration text for wireguard ready for copying or an error message for server interface.
    :rtype: str
    """
    profile = getUserProfile(user=user) 
    if not profile.verified:
        return 'Nejste ověřeni, kontaktujte správce pro ověření'
    
    clientInterface = selectInterfaceFromKey(key)
    if (clientInterface.interface_type == Interface.SERVER):
        return "Pro server nemůže být vrácená konfigurace."
    
    serverPeer = selectClientInterfacePeer(clientInterface)

    if (onlyVpn):
        return generateClientConfText( 
        clientInterface = clientInterface,
        serverPeer = serverPeer,
        endpoint = serverPeer.interface.server_endpoint,
        listenPort = serverPeer.interface.listen_port,
        allowedIPs = ipaddress.IPv4Interface(serverPeer.interface.ip_address).network)
    else:
        return generateClientConfText( 
            clientInterface = clientInterface,
            serverPeer = serverPeer,
            endpoint = serverPeer.interface.server_endpoint,
            listenPort = serverPeer.interface.listen_port)
    

def getUserProfile(user:User) -> Profile:
    """
    Gets the profile of a given user. The profile object contains additional information about user, mainly about wireguard.

    :param user: The user to get its profile.
    :param user: User

    :return: Profile object of the provided user
    :rtype: Profile
    """
    return selectUserProfile(user=user)

def createNewUser(form:CustomUserCreationForm) ->User:
    """
    Creates a new User with its profile.

    """
    user = form.save(commit=False)
    profile = createProfile(user=user)
    saveUser(user=user,profile=profile)
    form.save_m2m()
    return user

    
def checkUserOfKey(user:User , key: Key) -> bool:
    if (key.user == user or user.is_superuser or user.is_staff):
        return True
    return False

def getUsersKeys(user:User):
    return selectUserKeys(user=user)