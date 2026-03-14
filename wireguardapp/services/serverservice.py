import logging
from collections import defaultdict
from django.db import transaction
from django.contrib.auth.models import User
import ipaddress

from wireguardapp.models import Interface, Peer, Profile
from .wireguardcmd import (
    startWGserver, stopWGserver, isWGserverUp,
    getWGPeersState, selectAllNetworkInterfaces,
    addWGPeer, removeWGPeer, saveWgDump
)
from .modelfactory import ModelFactory 
from wireguardapp.database.repository import InterfaceRepository, PeerRepository, UserRepository, KeyRepository, ServerRepository

logger = logging.getLogger("wg")


class ServerService:
    # -------------------
    # Server Interface Getters
    # -------------------
    @staticmethod
    def getFirstServerInterface() -> Interface | None:
        return InterfaceRepository.getFirstServerInterface()

    @staticmethod
    def getServerInterfaceById(interfaceId: int) -> Interface | None:
        """
        Gets a server interface from its own id.

        :param interfaceId: Id of the server interface
        :type interfaceId: int

        :return: The interface of the given id
        :rtype: Interface
        """
        return InterfaceRepository.getById(interfaceId=interfaceId)

    @staticmethod
    def getAllServerInterfaces():
        """
        Gets all server interfaces of the server.

        :return: All interfaces of the type server.
        :rtype: QuerySet[Interface]
        """
        return InterfaceRepository.getAllServerInterfaces()

    # -------------------
    # WireGuard Control
    # -------------------
    @staticmethod
    def startServer(serverInterface: Interface, interfaceInternetName: str):
        """ 
        Tries to start the wireguard server interface service. See `wireguard.startWGserver` for more.
        Also increments session number of the server interface.
        """
        InterfaceRepository.incrementSession(interface=serverInterface)
        result = startWGserver(serverInterface, interfaceInternetName)
        saveWgDump(serverInterface)
        return result

    @staticmethod
    def stopServer(serverInterface: Interface):
        """ Tries to stop the wireguard server interface service. See `wireguard.stopWGserver` for more."""
        return stopWGserver(serverInterface)

    @staticmethod
    def checkServer(serverInterface: Interface):
        """ Checks if the server interface is running or stopped. See `wireguard.isWGserverUp` for more."""
        return isWGserverUp(serverInterface)

    # -------------------
    # Server Creation / Removal
    # -------------------
    @staticmethod
    def createNewServer(name: str, ipNetwork: str, networkMask: str, endpoint: str, port: str, clientToClient: bool) -> str | None:
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

        :param clientToClient: If checked True, clients will be able to communicate through this server interface.
        :type clientToClient: bool

        :return: None if executed without errors, string for a message what kind of error happened to send back to the web page form.
        :rtype: None | str
        """
        try:
            key = ModelFactory.createKey(user=None, name=name)
            interface = ModelFactory.createServerInterface(key, ipNetwork, networkMask, endpoint, port, clientToClient)
        except ValueError:
            return "Hodnoty nového server rozhraní nejsou validní."
        except Exception:
            return "Selhalo vytváření nového rozhraní serveru."
        ServerRepository.saveServer(key, interface)
        return None

    @staticmethod
    def removeServer(serverInterface: Interface):
        """
        Removes the server interface by the given interface.
        It will try to stop the server wireguard interface first, then deletes the server key.
        The deleted key will cascade to its interface.

        :param serverInterface: The server interface to be deleted
        :type serverInterface: Interface
        """
        ServerService.stopServer(serverInterface)
        ServerRepository.deleteServer(serverInterface.interface_key)

    # -------------------
    # Peer Management
    # -------------------
    @staticmethod
    def getServerInterfacePeers(serverInterface: Interface):
        """
        Gets the peers of the `serverInterface`.

        :param serverInterface: The interface to return its own peer objects.
        :type serverInterface: Interface

        :return: The peers of the given interface.
        :rtype: QuerySet[Peer]
        """
        return PeerRepository.getPeersByInterface(serverInterface)

    @staticmethod
    def getWgPeerConnectionState(serverInterface: Interface):
        """
        This function accesses the wireguard service for the `getWGPeersState` function.

        Uses the command ``wg show <interface_name> dump`` through a privileged script to read the
        current state of all peers attached to the server interface.

        A peer is considered connected if:

        - ``latest_handshake > 0``
        - The last handshake occurred within the past 120 seconds.

        :param serverInterface: The server interface to get its own peers.
        :type serverInterface: Interface

        :return: A list of dictionaries, one per peer, with the structure or a empty list
            of command execution fails.
        :rtype: list[dict]

        List structure
        ------------------
        The list of values will be in this form:
        .. code-block:: python

            [
                {
                    "peer": str,          # Peer string representation
                    "endpoint": str,      # Peer endpoint (ip:port) or "—"
                    "handshake": int,     # Unix timestamp (seconds)
                    "rx": int,            # Received bytes
                    "tx": int,            # Transmitted bytes
                    "is_connected": bool  # True if handshake < 120 seconds ago
                },
            ]


        """
        return getWGPeersState(serverInterface)

    @staticmethod
    def getInterfacePeersTotalBytes(serverInterface: Interface) -> list[dict]:
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
        peers = ServerService.getServerInterfacePeers(serverInterface)
        ranked = PeerRepository.getOrderedSnapshotsFromInterface(serverInterface)
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

    @staticmethod
    def getNetworkInterfaces():
        return selectAllNetworkInterfaces()

    # -------------------
    # User Management
    # -------------------
    @staticmethod
    def getAllClientUsers():
        """
        Gets all users that aren not superuser of staff.

        :return: All users that have the field `is_superuser` False
        :rtype: QuerySet[User]
        """
        return UserRepository.getAllNonAdminUsers()

    @staticmethod
    def switchVerifyProfile(userId: int) -> Profile:
        user = UserRepository.getById(userId)
        profile = UserRepository.getOrCreateProfile(user)

        if profile.verified:
            UserRepository.updateProfile(profile, verified=False)
            ServerService.disconnectUserFromWg(user)
        else:
            UserRepository.updateProfile(profile, verified=True)
            ServerService.connectUserToWg(user)

        return UserRepository.getOrCreateProfile(user)

    @staticmethod
    def connectUserToWg(user: User):
        peers = PeerRepository.getByUser(user)
        for peer in peers:
            try:
                addWGPeer(
                    serverInterfaceName=peer.interface.name,
                    peerKey=peer.peer_interface.interface_key.public_key,
                    ipAddress=peer.peer_interface.ip_address
                )
            except Exception as e:
                logger.warning(f"Failed to connect user peer: {e}")

    @staticmethod
    def disconnectUserFromWg(user: User):
        peers = PeerRepository.getByUser(user)
        for peer in peers:
            try:
                removeWGPeer(
                    serverInterfaceName=peer.interface.name,
                    peerKey=peer.peer_interface.interface_key.public_key
                )
            except Exception as e:
                logger.warning(f"Failed to disconnect user peer: {e}")

    @staticmethod
    def removeUser(userId: int) -> str | None:
        user = UserRepository.getById(userId)
        if not user:
            return "Uživatel nenalezen"

        ServerService.disconnectUserFromWg(user)
        UserRepository.delete(user)
        return None

    # -------------------
    # Server Update
    # -------------------
    @staticmethod
    def updateServer(interface: Interface, changed: list[str]):
        try:
            with transaction.atomic():
                if "ip_network" in changed or "ip_network_mask" in changed:
                    ServerService.updateServerPeersIpAddresses(interface)
                if "server_endpoint" in changed:
                    InterfaceRepository.updateEndpoint(interface, interface.server_endpoint)
                if "listen_port" in changed:
                    InterfaceRepository.updatePort(interface, interface.listen_port)
                if "client_to_client" in changed:
                    InterfaceRepository.updateClientToClient(interface, interface.client_to_client)
        except ValueError as e:
            return str(e)
        except Exception:
            return "Nastala chyba při aktualizaci serveru"

    @staticmethod
    def updateServerPeersIpAddresses(serverInterface: Interface):
        network = ipaddress.ip_network(f"{serverInterface.ip_network}/{serverInterface.ip_network_mask}")
        logger.info(f"network: {network}")
        
        clients = InterfaceRepository.getClientInterfacesFromServer(serverInterface)
        count = network.num_addresses - 2
        if count < len(clients) + 1:
            raise ValueError("Velikost sítě není dostačující pro všechny klienty")

        InterfaceRepository.updateNetwork(serverInterface, serverInterface.ip_network, serverInterface.ip_network_mask)

        hosts = network.hosts()
        InterfaceRepository.updateIpAddress(serverInterface, next(hosts))
        for client in clients:
            InterfaceRepository.updateIpAddress(client, next(hosts))