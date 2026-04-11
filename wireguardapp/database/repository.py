from wireguardapp.models import Interface, Peer, PeerSnapshot, Key, Profile
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber
import datetime
from django.utils import timezone
from datetime import timedelta


OLD_LOG_DAYS_CUTOFF = 30

# --------------------------
# Key Repository
# --------------------------
class KeyRepository:
    @staticmethod
    def save(key: Key):
        """ Saves the instance of a key"""
        key.save()

    @staticmethod
    def delete(key: Key):
        """Deletes the key of this instance."""
        key.delete()

    @staticmethod
    def getAllKeys():
        """ Gets all keys."""
        return Key.objects.all()

    @staticmethod
    def updateName(key: Key, name: str):
        """Updates the name of the key by the given name. """
        key.name = name
        key.save(update_fields=['name'])

    @staticmethod
    def getById(keyId: int) -> Key | None:
        """ Gets a key based on its id, None if it does not exists. """
        return Key.objects.filter(id=keyId).first()

    @staticmethod
    def getByUser(user: User):
        """ Gets all keys owned by the given user"""
        return Key.objects.filter(user=user)
    
    @staticmethod
    def getByPublicKey(publicKey : str):
        """ Gets the key based on `public_key` field, None if it does not exists. """
        return Key.objects.filter(public_key = publicKey).first()


# --------------------------
# Interface Repository
# --------------------------
class InterfaceRepository:
    @staticmethod
    def save(interface: Interface):
        """ Saves the given interface instance. """
        interface.save()

    @staticmethod
    def getAllInterfaces():
        """ Gets all interfaces. """
        return Interface.objects.all()

    @staticmethod
    def getFirstServerInterface() -> Interface | None:
        """ Test method that returns a first server interface. """
        return Interface.objects.filter(interface_type=Interface.SERVER).first()

    @staticmethod
    def getAllServerInterfaces():
        """ Returns all interfaces with `interface_type` value server. """
        return Interface.objects.filter(interface_type=Interface.SERVER)
    
    @staticmethod
    def getClientsServerInterface(clientKey):
        """ 
        Returns the server interface of the given client key.
        Client key is the key, that connects to the server interface that will be returned.  
        """
        clientPeer = Peer.objects.filter(peer_interface__interface_key=clientKey).first()
        return clientPeer.interface if clientPeer else None

    @staticmethod
    def getById(interfaceId: int) -> Interface | None:
        """ Returns an interface by its own `id`. """
        return Interface.objects.filter(id=interfaceId).first()

    @staticmethod
    def getByKey(interfaceKey: Key) -> Interface | None:
        """ Returns an interface by its own `interface_key`. """
        return Interface.objects.filter(interface_key=interfaceKey).first()

    @staticmethod
    def getByName(name: str):
        """ Returns an interface by its own name (system name) `name`. """
        return Interface.objects.filter(name=name)

    @staticmethod
    def getClientInterfacesFromServer(serverInterface: Interface):
        """ Returns all client interfaces that connects to the given server interface. """
        peers = Peer.objects.filter(interface=serverInterface).select_related("peer_interface")
        return [peer.peer_interface for peer in peers]

    @staticmethod
    def updateEndpoint(interface: Interface, endpoint: str):
        """ Updates the endpoint [`server_endpoint`] of the given interface. """
        interface.server_endpoint = endpoint
        interface.save(update_fields=['server_endpoint'])

    @staticmethod
    def updatePort(interface: Interface, port: int):
        """ Updates the port [`listen_port`] of the given interface. """
        interface.listen_port = port
        interface.save(update_fields=['listen_port'])

    @staticmethod
    def updateIpAddress(interface: Interface, ipAddress: str):
        """ Updated the ip address [`ip_address`] of the given interface """
        interface.ip_address = ipAddress
        interface.save(update_fields=['ip_address'])

    @staticmethod
    def updateNetwork(interface: Interface, ipNetwork: str, mask: str):
        """ Updates the ip network and mask [`ip_network`,`ip_network_mask`] of the given interface. """
        interface.ip_network = ipNetwork
        interface.ip_network_mask = mask
        interface.save(update_fields=['ip_network', 'ip_network_mask'])

    @staticmethod
    def updateClientToClient(interface: Interface, clientToClient: bool):
        """ Updates the client to client [`client_to_client`] of the given interface. """
        interface.client_to_client = clientToClient
        interface.save(update_fields=['client_to_client'])

    @staticmethod
    def incrementSession(interface: Interface):
        """ Adds 1 to the `session_number` to the given interface. """
        interface.session_number += 1
        interface.save(update_fields=['session_number'])


# --------------------------
# Peer Repository
# --------------------------
class PeerRepository:
    @staticmethod
    def save(peer: Peer):
        """ Saves the peer instance. """
        peer.save()

    @staticmethod
    def saveState(peer:Peer):
        """ Save the fields `total_rx_bytes`, `total_tx_bytes`, `last_rx_bytes`, `last_tx_bytes` of the instance"""
        peer.save(update_fields=
                ['total_rx_bytes',
                    'total_tx_bytes',
                    'last_rx_bytes',
                    'last_tx_bytes'])

    @staticmethod
    def getAllPeers():
        """ Gets all peers. """
        return Peer.objects.all()

    @staticmethod
    def getPeersByInterface(interface: Interface):
        """ Returns all peer of a server interface interface """
        return Peer.objects.filter(interface=interface)

    @staticmethod
    def getVerifiedPeersFromServer(serverInterface: Interface):
        """ Returns all peers with verified users. """
        return Peer.objects.filter(
            interface=serverInterface,
            peer_interface__interface_key__user__profile__verified=True
        )

    @staticmethod
    def getClientInterfacePeer(interface: Interface) -> Peer | None:
        """ Returns the clients peer. """
        return Peer.objects.filter(peer_interface=interface).first()

    @staticmethod
    def getByUser(user: User):
        """ Returns all clients peers of the user. """
        return Peer.objects.filter(peer_interface__interface_key__user=user)
    
    @staticmethod
    def getPeerFromKey(key: Key) -> Peer | None:
        """ Returns a client peer from its key. """
        return Peer.objects.filter(peer_interface__interface_key=key).first()
    

    @staticmethod
    def getOrderedSnapshotsFromInterface(serverInterface: Interface):
        """ Retuns all peer snapshots of the given interface. Adds `row_number` to each row. Grouped by peer and Ordered by collected_at descending. """
        return PeerSnapshot.objects.annotate(
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F('peer')],
                order_by=F('collected_at').desc()
            )
        ).filter(peer__interface=serverInterface)
    
    @staticmethod
    def getOrderedSnapshotsFromPeer(peer: Peer):
        """ Returns all peer snapshots of the given peer. Adds `row_number` to each row. Ordered by collected_at descending. """
        return PeerSnapshot.objects.annotate(
            row_number=Window(
                expression=RowNumber(),
                order_by=F('collected_at').desc()
            )
        ).filter(peer=peer)


# --------------------------
# User Repository
# --------------------------
class UserRepository:
    @staticmethod
    def save(user: User, profile: Profile):
        """ Saves the user and profile instances. """
        user.save()
        profile.save()

    @staticmethod
    def delete(user: User):
        """ Deletes a user. """
        user.delete()

    @staticmethod
    def getById(userId: int) -> User | None:
        """ Returns a user from its own id. """
        return User.objects.filter(pk=userId).first()

    @staticmethod
    def getAllNonAdminUsers():
        """ Returns all users that are not admin or staff. """
        return User.objects.exclude(is_superuser=True)

    @staticmethod
    def getOrCreateProfile(user: User) -> Profile:
        """ Returns a profile of the user. Creates a profile of the user if it does not exists. """
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def updateProfile(profile: Profile, verified: bool = None, keyLimit: int = None, keyCount: int = None):
        """
        Updates fields of the given profile based on parameters.
        """
        fields = []
        if verified is not None:
            profile.verified = verified
            fields.append('verified')
        if keyLimit is not None:
            profile.key_limit = keyLimit
            fields.append('key_limit')
        if keyCount is not None:
            profile.key_count = keyCount
            fields.append('key_count')
        if fields:
            profile.save(update_fields=fields)

class PeerSnapshotRepository:
    @staticmethod
    def save(snapshot :PeerSnapshot):
        """Saves the peer snapshot. """
        snapshot.save()
    
    def deleteOldSnapShots():
        cutoff = timezone.now() - timedelta(days=OLD_LOG_DAYS_CUTOFF)
        PeerSnapshot.objects.filter(created_at__lt=cutoff).delete()



# --------------------------
# High-level Operations
# --------------------------
class ClientRepository:
    @staticmethod
    def saveClient(clientKey: Key, clientInterface: Interface, serverPeer: Peer):
        """Atomic save of client objects. """
        with transaction.atomic():
            KeyRepository.save(clientKey)
            InterfaceRepository.save(clientInterface)
            PeerRepository.save(serverPeer)
            profile = UserRepository.getOrCreateProfile(clientKey.user)
            UserRepository.updateProfile(profile=profile, keyCount=profile.key_count + 1)

    @staticmethod
    def deleteClient(clientKey: Key):
        """Deletes the client (cascades to interface and peers)."""
        with transaction.atomic():
            KeyRepository.delete(clientKey)
            profile = UserRepository.getOrCreateProfile(clientKey.user)
            UserRepository.updateProfile(profile=profile, keyCount=profile.key_count - 1)


class ServerRepository:
    @staticmethod
    def saveServer(serverKey: Key, serverInterface: Interface):
        """ Atomic save of server objects. """
        with transaction.atomic():
            KeyRepository.save(serverKey)
            InterfaceRepository.save(serverInterface)

    @staticmethod
    def deleteServer(serverKey: Key):
        """ Deletes a server. """
        with transaction.atomic():
            server = InterfaceRepository.getByKey(serverKey)
            clientInterfaces = InterfaceRepository.getClientInterfacesFromServer(server)
            for client in clientInterfaces:
                ClientRepository.deleteClient(client.interface_key)
            KeyRepository.delete(serverKey)