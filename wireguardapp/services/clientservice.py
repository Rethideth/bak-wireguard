import logging
from django.contrib.auth.models import User
from wireguardapp.models import Interface, Key, Profile, Peer
from wireguardapp.database.repository import InterfaceRepository, PeerRepository, UserRepository, KeyRepository, ClientRepository
from .wireguardcmd import addWGPeer, removeWGPeer, generateClientConfText
from .modelfactory import ModelFactory
import ipaddress

logger = logging.getLogger("wg")

class ClientService:
    # -------------------
    # Key & Interface & Peer Access
    # -------------------
    @staticmethod
    def getKeyById(keyId: int) -> Key | None:
        """
        Tries to get Key object instance from its id if it exists. 

        :param keyId: The id of the searched Key object
        :type keyId: int

        :return: Key object instance with the same provided id.
        :rtype: Key | None
        """
        return KeyRepository.getById(keyId=keyId)

    @staticmethod
    def getClientsServerInterface(clientKey: Key) -> Interface | None:
        """
        Gets the server interface that the given client key is connected to.
        This doesnt return the interface owned by the given client key.

        :param clientKey: The key object to return its own server interface.
        :type clientKey: Key

        :return: The server interface that the client key is connected to if it exists.
        :rtype: Interface | None 
        """
        return InterfaceRepository.getClientsServerInterface(clientKey)
    
    @staticmethod
    def getInterfaceFromKey(key: Key):
        return InterfaceRepository.getByKey(key)

    @staticmethod
    def getUserProfile(user: User) -> Profile:
        """
        Gets the profile of a given user. The profile object contains additional information about user, mainly about wireguard.

        :param user: The user to get its profile.
        :param user: User

        :return: Profile object of the provided user
        :rtype: Profile
        """
        return UserRepository.getOrCreateProfile(user=user)

    @staticmethod
    def getUserKeys(user: User):
        """
        Gets all keys owned by the given user.

        :param user: The user to returns its owned keys.
        :type user: User

        :return: All keys owned by the given keys
        :rtype: QuerySet[Key]
        """
        return KeyRepository.getByUser(user)

    @staticmethod
    def checkUserOfKey(user: User, key: Key) -> bool:
        """
        Checks if the given key is owned by the given user, or if the user is staff.

        :param user: The user to check its ownership of the given key
        :type user: User

        :param key: The key to check its user.
        :type key: Key

        :return: True if the user owns the key or if the user is staff or superuser.
        :rtype: bool
        """
        return key.user == user or user.is_superuser or user.is_staff
    
    @staticmethod
    def changeKeyName(key: Key, name: str):
        """
        Changes the name of the given key.

        :param key: The key to change its name.
        :type key: Key

        :param name: The string value to change the name of the key to.
        :type name: str
        """
        return KeyRepository.updateName(key, name)
    
    @staticmethod
    def getPeerFromKey(key: Key) -> Key | None:
        """
        Gets the peer of the given key if exists.
        The peer that the client connect to the server interface.

        :param key: The clients key that is used to connect to the server interface.
        :type key: Key

        :return: The peer object of the client.
        :rtype: Peer
        """
        return PeerRepository.getPeerFromKey(key)
    

    @staticmethod
    def stripPort(address: str) -> str:
        if address == None:
            return address
        address = address.strip()

        # IPv6 ve formátu [addr]:port
        if address.startswith('['):
            if ']' in address:
                return address[1:address.index(']')]
            return address  # fallback

        # zkus rovnou jestli to není čistá IP
        try:
            ipaddress.ip_address(address)
            return address
        except ValueError:
            pass

        # rozděl na IP + port (poslední :)
        if ':' in address:
            ip_part, port_part = address.rsplit(':', 1)

            # port musí být číslo
            if port_part.isdigit():
                try:
                    ipaddress.ip_address(ip_part)
                    return ip_part
                except ValueError:
                    pass

        return address
    
    @staticmethod
    def getEndpointOfPeer(peer: Peer) -> set[str]:
        """
        Gets all the endpoint of the peer life through peer snapshots.

        :param peer: The peer to get all the endpoints it had used.
        :type peer: Peer

        :return: All different endpoints of the peer that snapshots captured.
        :rtype: set[str]
        """
        ranked = PeerRepository.getOrderedSnapshotsFromPeer(peer)

        endpoints = set()
        for snap in ranked:
            endpoints.add(ClientService.stripPort(snap.endpoint))

        try: 
            endpoints.remove(None)
        except Exception:
            pass
        return endpoints

    # -------------------
    # Client Creation
    # -------------------
    @staticmethod
    def createNewClient(user: User, name: str, serverInterface: Interface) -> str | None:
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
        profile = ClientService.getUserProfile(user)
        
        if not profile.verified:
            return "Nejste ověřeni"
        if profile.key_limit <= profile.key_count:
            return "Dosáhli jste maximum počet klíču, co můžete mít."

        try:
            key = ModelFactory.createKey(user, name)
            interface = ModelFactory.createClientInterface(user, key, serverInterface)
            serverPeer = ModelFactory.createPeer(serverInterface, interface)
        except TypeError as e:
            return "Rozhraní pro alokaci ip adresy není typu server. " + str(e)
        except ValueError:
            return "Volné ip adresy pro tento server byly vyčerpány."
        except Exception:
            return "Nastala chyba při vytváření klienta."

        # Save all client models atomically
        ClientRepository.saveClient(clientKey=key, clientInterface=interface, serverPeer=serverPeer)
        

        # Add peer to WireGuard
        try:
            addWGPeer(
                serverInterfaceName=serverInterface.name,
                peerKey=interface.interface_key.public_key,
                ipAddress=interface.ip_address
            )
        except RuntimeError as e:
            logger.error(f"Failed to add WireGuard peer: {e}")

        return None

    # -------------------
    # Client Removal
    # -------------------
    @staticmethod
    def removeClient(user: User, key: Key) -> str | None:
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
        profile = ClientService.getUserProfile(user)
        if not profile.verified:
            return "Nejste ověřeni, kontaktujte správce pro ověření"

        serverInterface = InterfaceRepository.getClientsServerInterface(key)
        ClientRepository.deleteClient(key)
        

        # Remove from WireGuard
        try:
            removeWGPeer(
                serverInterfaceName=serverInterface.name,
                peerKey=key.public_key
            )
        except RuntimeError:
            pass

        return None

    # -------------------
    # WireGuard Configuration
    # -------------------
    @staticmethod
    def generateClientConf(user: User, key: Key, onlyVpn: bool = False) -> str:
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
        profile = ClientService.getUserProfile(user)
        if not profile.verified:
            return "Nejste ověřeni, kontaktujte správce pro ověření"
        
        clientInterface = InterfaceRepository.getByKey(key)
        if clientInterface.interface_type == Interface.SERVER:
            return "Pro server nemůže být vrácená konfigurace."
        
        serverPeer = PeerRepository.getClientInterfacePeer(clientInterface)
        
        if onlyVpn:
            allowedIps = f"{serverPeer.interface.ip_network}/{serverPeer.interface.ip_network_mask}"
            return generateClientConfText(
                clientInterface=clientInterface,
                serverPeer=serverPeer,
                endpoint=serverPeer.interface.server_endpoint,
                listenPort=serverPeer.interface.listen_port,
                allowedIPs=allowedIps
            )
        else:
            return generateClientConfText(
                clientInterface=clientInterface,
                serverPeer=serverPeer,
                endpoint=serverPeer.interface.server_endpoint,
                listenPort=serverPeer.interface.listen_port
            )

    # -------------------
    # User Management
    # -------------------
    @staticmethod
    def createUser(user : User) -> User:
        """
        Creates a profile of the user and saves them both.

        :param user: The user to create its own profile. It will be saved.
        :type user: User

        :return: The given user instance
        :rtype: User
        """
        profile = ModelFactory.createProfile(user)
        UserRepository.save(user=user, profile=profile)
        return user

    @staticmethod
    def getUserFromId(userId: int) -> User | None:
        """
        Gets an User object from its own id.

        :param id: The id of the seached user
        :type id: int

        :return: User if it exists, None if not
        :rtype: User | None 
        """
        return UserRepository.getById(userId=userId)