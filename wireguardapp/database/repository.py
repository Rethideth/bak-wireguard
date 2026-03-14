from wireguardapp.models import Interface, Peer, PeerSnapshot, Key, Profile
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import RowNumber

# --------------------------
# Key Repository
# --------------------------
class KeyRepository:
    @staticmethod
    def save(key: Key):
        key.save()

    @staticmethod
    def delete(key: Key):
        key.delete()

    @staticmethod
    def updateName(key: Key, name: str):
        key.name = name
        key.save(update_fields=['name'])

    @staticmethod
    def getById(keyId: int) -> Key | None:
        return Key.objects.filter(id=keyId).first()

    @staticmethod
    def getByUser(user: User):
        return Key.objects.filter(user=user)


# --------------------------
# Interface Repository
# --------------------------
class InterfaceRepository:
    @staticmethod
    def save(interface: Interface):
        interface.save()

    @staticmethod
    def getFirstServerInterface() -> Interface | None:
        return Interface.objects.filter(interface_type=Interface.SERVER).first()

    @staticmethod
    def getAllServerInterfaces():
        return Interface.objects.filter(interface_type=Interface.SERVER)
    
    @staticmethod
    def getClientsServerInterface(clientKey):
        clientPeer = Peer.objects.filter(peer_interface__interface_key=clientKey).first()
        return clientPeer.interface

    @staticmethod
    def getById(interfaceId: int) -> Interface | None:
        return Interface.objects.filter(id=interfaceId).first()

    @staticmethod
    def getByKey(interfaceKey: Key) -> Interface | None:
        return Interface.objects.filter(interface_key=interfaceKey).first()

    @staticmethod
    def getByName(name: str):
        return Interface.objects.filter(name=name)

    @staticmethod
    def getClientInterfacesFromServer(serverInterface: Interface):
        peers = Peer.objects.filter(interface=serverInterface).select_related("peer_interface")
        return [peer.peer_interface for peer in peers]

    @staticmethod
    def updateEndpoint(interface: Interface, endpoint: str):
        interface.server_endpoint = endpoint
        interface.save(update_fields=['server_endpoint'])

    @staticmethod
    def updatePort(interface: Interface, port: int):
        interface.listen_port = port
        interface.save(update_fields=['listen_port'])

    @staticmethod
    def updateIpAddress(interface: Interface, ipAddress: str):
        interface.ip_address = ipAddress
        interface.save(update_fields=['ip_address'])

    @staticmethod
    def updateNetwork(interface: Interface, ipNetwork: str, mask: str):
        interface.ip_network = ipNetwork
        interface.ip_network_mask = mask
        interface.save(update_fields=['ip_network', 'ip_network_mask'])

    @staticmethod
    def updateClientToClient(interface: Interface, clientToClient: bool):
        interface.client_to_client = clientToClient
        interface.save(update_fields=['client_to_client'])

    @staticmethod
    def incrementSession(interface: Interface):
        interface.session_number += 1
        interface.save(update_fields=['session_number'])


# --------------------------
# Peer Repository
# --------------------------
class PeerRepository:
    @staticmethod
    def save(peer: Peer):
        peer.save()

    @staticmethod
    def getPeersByInterface(interface: Interface):
        return Peer.objects.filter(interface=interface)

    @staticmethod
    def getVerifiedPeersFromServer(serverInterface: Interface):
        return Peer.objects.filter(
            interface=serverInterface,
            peer_interface__interface_key__user__profile__verified=True
        )

    @staticmethod
    def getClientInterfacePeer(interface: Interface) -> Peer | None:
        return Peer.objects.filter(peer_interface=interface).first()

    @staticmethod
    def getByUser(user: User):
        return Peer.objects.filter(peer_interface__interface_key__user=user)
    
    @staticmethod
    def getPeerFromKey(key: Key) -> Peer | None:
        return Peer.objects.filter(peer_interface__interface_key=key).first()

    @staticmethod
    def getServerInterfaceOfClient(clientKey: Key) -> Interface | None:
        clientPeer = Peer.objects.filter(peer_interface__interface_key=clientKey).first()
        return clientPeer.interface if clientPeer else None

    @staticmethod
    def getOrderedSnapshotsFromInterface(serverInterface: Interface):
        return PeerSnapshot.objects.annotate(
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F('peer')],
                order_by=F('collected_at').desc()
            )
        ).filter(peer__interface=serverInterface)
    
    @staticmethod
    def getOrderedSnapshotsFromPeer(peer: Peer):
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
        user.save()
        profile.save()

    @staticmethod
    def delete(user: User):
        user.delete()

    @staticmethod
    def getById(userId: int) -> User | None:
        return User.objects.filter(pk=userId).first()

    @staticmethod
    def getAllNonAdminUsers():
        return User.objects.exclude(is_superuser=True)

    @staticmethod
    def getOrCreateProfile(user: User) -> Profile:
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

# --------------------------
# High-level Operations
# --------------------------
class ClientRepository:
    @staticmethod
    def saveClient(clientKey: Key, clientInterface: Interface, serverPeer: Peer):
        """Atomic save of client Key, Interface, and server Peer."""
        with transaction.atomic():
            KeyRepository.save(clientKey)
            InterfaceRepository.save(clientInterface)
            PeerRepository.save(serverPeer)

    @staticmethod
    def deleteClient(clientKey: Key):
        """Deletes the client (cascades to interface and peers)."""
        KeyRepository.delete(clientKey)


class ServerRepository:
    @staticmethod
    def saveServer(serverKey: Key, serverInterface: Interface):
        with transaction.atomic():
            KeyRepository.save(serverKey)
            InterfaceRepository.save(serverInterface)

    @staticmethod
    def deleteServer(serverKey: Key):
        KeyRepository.delete(serverKey)