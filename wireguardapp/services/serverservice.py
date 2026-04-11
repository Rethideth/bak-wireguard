import logging
from collections import defaultdict
from django.db import transaction
from django.contrib.auth.models import User
import ipaddress
from django.db.models import Q

from wireguardapp.models import Interface, Peer, Profile,PeerSnapshot
from .wireguardcmd import (
    startWGserver, stopWGserver, isWGserverUp,
    getWGPeersState, selectAllNetworkInterfaces,
    addWGPeer, removeWGPeer,getWgDump
)
from .modelfactory import ModelFactory 
from wireguardapp.database.repository import InterfaceRepository, PeerRepository, UserRepository, KeyRepository, ServerRepository,PeerSnapshotRepository
import datetime
from django.utils import timezone

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

        If starting of the interface failed, returns the error message.

        :param serverInterface: The server interface to start.
        :type serverInterface: Interface

        :param interfaceInternetName: The name of a interface to forward wireguard data transfer to. It needs to have a internet access to function.
            Usualy it will be 'eth0'.
        :type interfaceInternetName: 

        :return: None if scripts executed succesfully, an error value if error happened during the executing proccess.
        :rtype: None | str
        """
        if interfaceInternetName == '':
            return "Síťové rozhraní pro přesměrování přenosu chybí."
        result = startWGserver(serverInterface, interfaceInternetName)
        ServerService.saveServerInterfacePeersState(serverInterface)
        return result

    @staticmethod
    def stopServer(serverInterface: Interface):
        """ 
        Tries to stop the wireguard server interface service. See `wireguard.stopWGserver` for more.

        :param serverInterface: The server interface to stop.
        :type serverInterface: Interface
        
        :return: None if scripts executed succesfully, an error value if error happened during the executing proccess.
        :rtype: None | str
        """
        return stopWGserver(serverInterface)

    @staticmethod
    def checkServer(serverInterface: Interface):
        """ 
        Checks if the server interface is running or stopped. See `wireguard.isWGserverUp` for more.
        
        :param serverInterface: The server interface to check if it is running.
        :type serverInterface: Interface

        :return: Return True if interface is running, False if it is stopped. 
        :rtype: bool
        """
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
        logger.info(f"({datetime.datetime.now()}):New interface {interface.name}-{key.name} created.")
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
        logger.info(f"({datetime.datetime.now()}):Interface {serverInterface.name}-{serverInterface.interface_key.name} deleted.")

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
    def getServerInterfacePeersFiltered(serverInterface: Interface, field :str, value : str):
        """
        Gets filtered peers of the `serverInterface`.

        :param serverInterface: The interface to return its own peer objects.
        :type serverInterface: Interface

        :param field: The field to filter peers. Choices are `user` to filter by username or first or last name,
          `ip` to filter based on the ip address of a peer, `name` to filter based on peer key name.
        :type field: str

        :param value: The value of the field to filter peers.
        :type value: str

        :param serverInterface: The interface to return its own peer objects.
        :type serverInterface: Interface

        :return: The peers of the given interface.
        :rtype: QuerySet[Peer]
        """
        peers = PeerRepository.getPeersByInterface(serverInterface)

        if value:
            if field == "user":
                peers = peers.filter(
                    Q(peer_interface__interface_key__user__username__icontains=value) |
                    Q(peer_interface__interface_key__user__first_name__icontains=value) |
                    Q(peer_interface__interface_key__user__last_name__icontains=value)
                )

            elif field == "ip":
                peers = peers.filter(
                    peer_interface__ip_address__icontains=value
                )

            elif field == "name":
                peers = peers.filter(
                    peer_interface__interface_key__name__icontains=value
                )
        return peers


    @staticmethod
    def getWgPeerConnectionState(serverInterface: Interface, field : str = None, value : str = None, state : str = None):
        """
        This function accesses the wireguard service for the `getWGPeersState` function. Will filter the output
        based on the given field and value and by state of connection.

        Uses the command ``wg show <interface_name> dump`` through a privileged script to read the
        current state of all peers attached to the server interface.

        A peer is considered connected if:

        - ``latest_handshake > 0``
        - The last handshake occurred within the past 120 seconds.

        :param serverInterface: The server interface to get its own peers.
        :type serverInterface: Interface

        :param field: The name of the field to filter the result. Choices are: `user` for the name of a user,
        `ip` for the ip addres of the peer, `name` for the name of the peer key. Anything else is ignored.
        :type field: str

        :param value: The value of the field parameter to be filtered.
        :type value: str

        :param state: The state of the peer to be filtered. If None, result wont be filtered. 
        :type state: str

        :return: A tuple of a list of dictionaries and count of online peers. Each entry of the list equals to one peer, with the structure below or a empty list
        of command execution fails.
        :rtype: tuple[list[dict],int]

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
        return getWGPeersState(serverInterface,field,value,state)



    @staticmethod
    def getNetworkInterfaces():
        """
        Gets the names of all current network interfaces of the current device.

        :returns: List of interfaces names e.g. ['eth0', 'wlo0']
        :rtype: list[str]
        """
        return selectAllNetworkInterfaces()
    
    @staticmethod
    def saveAllPeersState():
        """
        Runs the `getWgDump` for every server interface in the database. 
        Saves the snapshot of every enabled peer and aggregate its data into peer object.
        Also deletes month old snapshots.
        """
        interfaces = InterfaceRepository.getAllServerInterfaces()

        for interface in interfaces:
            ServerService.saveServerInterfacePeersState(interface=interface)
        PeerSnapshotRepository.deleteOldSnapShots()

    @staticmethod
    def saveServerInterfacePeersState(interface :Interface):
        """
        Saves the state on the given interface based on the command 'wg show <interface.name> dump'.
        The information is saved in PeerSnapshot models and aggregated in peer object (total send/recieved bytes)

        If the interface in not up, it skips saving data.

        :param interface: The interface to save its own dump.
        :type interface: Interface
        """
        try:
            lines = getWgDump(interface=interface)
        except:
            return
        i = 0

        # First line is interface info → skip it
        for line in lines[1:]:
            parts = line.split("\t")

            public_key = parts[0]
            endpoint = parts[2]
            latest_handshake = int(parts[4])
            rx_bytes = int(parts[5])
            tx_bytes = int(parts[6])
            keepalive = parts[7]

            peer = PeerRepository.getPeerFromKey(KeyRepository.getByPublicKey(public_key))
            
            if latest_handshake == 0: 
                handshake_dt = None
            else:
                naive_dt = datetime.datetime.fromtimestamp(latest_handshake)
                handshake_dt = timezone.make_aware(naive_dt)


            snapshot = ModelFactory.createPeerSnapshot(
                peer=peer,
                endpoint=endpoint,
                handshake_dt=handshake_dt,
                rx_bytes=rx_bytes,
                tx_bytes=tx_bytes,
                serverInterface=interface
            )
            PeerSnapshotRepository.save(snapshot)
            # Update peer state

            currentRx = rx_bytes
            currentTx = tx_bytes

            # was interface reseted?
            if (peer.last_rx_bytes > currentRx or
                peer.last_tx_bytes > currentTx):
                diffR = currentRx
                diffT = currentTx
            else:
                diffR = currentRx - peer.last_rx_bytes
                diffT = currentTx - peer.last_tx_bytes

            peer.total_rx_bytes += diffR
            peer.total_tx_bytes += diffT
            peer.last_rx_bytes = currentRx
            peer.last_tx_bytes = currentTx

            PeerRepository.saveState(peer)

            i += 1
        logger.info(f"({datetime.datetime.now()}):{interface.name}-{interface.interface_key.name} saved states of {i} peers.")

    # -------------------
    # User Management
    # -------------------
    @staticmethod
    def getAllClientUsers():
        """
        Gets all users that are not superuser.

        :return: All users that have the field `is_superuser` False
        :rtype: QuerySet[User]
        """
        return UserRepository.getAllNonAdminUsers()

    @staticmethod
    def getAllClientUsersFiltered(name : str, username : str, email : str, verified : str):
        """
        Gets all users that are not superuser. This querySet is filtered by the given paramenters.

        :param name: The name of the searched User. Includes fields `first_name` and `last_name`.
        :type name: str

        :param username: The username of the searched User.
        :type username: str

        :param email: The email of the searched User.
        :type email: str

        :param verified: The verification state of the seached User. Choices are either `true` or `false`, otherwise the field is not filtered.
        :type verified: str

        :return: All users that have the field `is_superuser` False and filtered by the given parameters.
        :rtype: QuerySet[User]
        """
        clients = ServerService.getAllClientUsers()

        if name:
            clients = clients.filter(
                Q(first_name__icontains=name) |
                Q(last_name__icontains=name)
            )

        if username:
            clients = clients.filter(username__icontains=username)

        if email:
            clients = clients.filter(email__icontains=email)

        if verified == "true":
            clients = clients.filter(profile__verified=True)
        elif verified == "false":
            clients = clients.filter(profile__verified=False)

        return clients


    @staticmethod
    def switchVerifyProfile(userId: int) -> Profile:
        """
        Swithes the verification of the User by the given id. Also connects or disconnects based on their verification status.

        :param userId: The id of the user to switch the verification status.
        :type userId: int

        :return: The current profile of the user after the switch.
        :rtype: Profile

        """
        user = UserRepository.getById(userId)
        profile = UserRepository.getOrCreateProfile(user)

        if profile.verified:
            UserRepository.updateProfile(profile, verified=False)
            ServerService.disconnectUserFromWg(user)
            logger.info(f"({datetime.datetime.now()}):User {user.email} was unverified and disconnected")
        else:
            UserRepository.updateProfile(profile, verified=True)
            ServerService.connectUserToWg(user)
            logger.info(f"({datetime.datetime.now()}):User {user.email} was verified and connected")

        return UserRepository.getOrCreateProfile(user)

    @staticmethod
    def connectUserToWg(user: User):
        """
        Connect all WireGuard peers to their server interfaces of their given user.

        :param user: The user to connect its peer to their selected server interface.
        :type user: User
        """
        peers = PeerRepository.getByUser(user)
        for peer in peers:
            try:
                addWGPeer(
                    serverInterfaceName=peer.interface.name,
                    peerKey=peer.peer_interface.interface_key.public_key,
                    ipAddress=peer.peer_interface.ip_address
                )
            except Exception as e:
                logger.error(f"Failed to connect user peer: {e}")

    @staticmethod
    def disconnectUserFromWg(user: User):
        """
        Disconnects all WireGuard peers from their server interfaces of their given user.

        :param user: The user to disconnect its peer from their selected server interface.
        :type user: User
        """
        peers = PeerRepository.getByUser(user)
        for peer in peers:
            try:
                removeWGPeer(
                    serverInterfaceName=peer.interface.name,
                    peerKey=peer.peer_interface.interface_key.public_key
                )
            except Exception as e:
                logger.error(f"Failed to disconnect user peer: {e}")

    @staticmethod
    def removeUser(userId: int) -> str | None:
        """
        Removes the given user and disconect its own peers from the WireGuard server interface.

        :param userId: The id of the user to remove and disconnect from WireGuard server interface.
        :type userId: int

        :return: None if succesful, returns an error message if user was not found.
        :rtype: str| None
        """
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
        """
        Saves the altered information of the given interface. The information is changed based on the changed values.
        The saving is in a transaction.

        :param interface: The interface to change its own information. The changed values are alredy in the interface instance.
        :type interface: Interface

        :param changed: The list of values that are changed in the interface instance.
        The values that will be altered are: `ip_network`, `ip_network_mask`, `server_endpoint`, `listen_port`, `client_to_client`
        :type: list[str]

        :return: None if no errors happened, a string value if yes.
        :rtype: None | str
        """
        oldInterface = InterfaceRepository.getById(interface.pk)
        try:
            with transaction.atomic():
                if "ip_network" in changed or "ip_network_mask" in changed:
                    ServerService.updateServerPeersIpAddresses(interface)
                    logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} " +
                                f"changed ip network {oldInterface.ip_network}/{oldInterface.ip_network_mask} -> {interface.ip_network}/{interface.ip_network_mask}.")
                if "server_endpoint" in changed:
                    InterfaceRepository.updateEndpoint(interface, interface.server_endpoint)
                    logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} "+
                                f"changed server endpoint {oldInterface.server_endpoint} -> {interface.server_endpoint}.")
                if "listen_port" in changed:
                    InterfaceRepository.updatePort(interface, interface.listen_port)
                    logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} "+
                                f"changed listen port {oldInterface.listen_port} -> {interface.listen_port}.")
                if "client_to_client" in changed:
                    InterfaceRepository.updateClientToClient(interface, interface.client_to_client)
                    logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} "+
                                f"changed client to client connection {oldInterface.client_to_client} -> {interface.client_to_client}.")
        except ValueError as e:
            logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} failed to change ip network: {str(e)}.")
            return str(e)
        except Exception as e:
            logger.info(f"({datetime.datetime.now()}):Interface {interface.name}-{interface.interface_key.name} failed to change a value: {str(e)}.")
            return "Nastala chyba při aktualizaci serveru: "+ str(e)
        
        
    @staticmethod
    def updateServerPeersIpAddresses(serverInterface: Interface):
        """
        Saves the altered network information of the given server interface. 
        Also changes the network information of all clients of the server interface.
        Raises a `ValueError` if the network is not big enough for the server interface network or the values are not an ip address and mask.

        :param serverInterface: The server interface with the altered `ip_network` or `ip_network_mask`.
        :type serverInterface: Interface

        :raises ValueError: Raised if the network is not suitable or the `ip_network` or `ip_network_mask` are not in the corrent format.
        """
        network = ipaddress.ip_network(f"{serverInterface.ip_network}/{serverInterface.ip_network_mask}")
        
        clients = InterfaceRepository.getClientInterfacesFromServer(serverInterface)
        count = network.num_addresses - 2
        if count < len(clients) + 1:
            raise ValueError("Velikost sítě není dostačující pro všechny klienty")

        InterfaceRepository.updateNetwork(serverInterface, serverInterface.ip_network, serverInterface.ip_network_mask)

        hosts = network.hosts()
        InterfaceRepository.updateIpAddress(serverInterface, next(hosts))
        for client in clients:
            InterfaceRepository.updateIpAddress(client, next(hosts))