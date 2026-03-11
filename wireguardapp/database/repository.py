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
    def update_name(key: Key, name: str):
        key.name = name
        key.save(update_fields=['name'])

    @staticmethod
    def get_by_id(key_id: int) -> Key | None:
        return Key.objects.filter(id=key_id).first()

    @staticmethod
    def get_by_user(user: User):
        return Key.objects.filter(user=user)


# --------------------------
# Interface Repository
# --------------------------
class InterfaceRepository:
    @staticmethod
    def save(interface: Interface):
        interface.save()

    @staticmethod
    def get_first_server_interface() -> Interface | None:
        return Interface.objects.filter(interface_type=Interface.SERVER).first()

    @staticmethod
    def get_all_server_interfaces():
        return Interface.objects.filter(interface_type=Interface.SERVER)
    
    @staticmethod
    def get_clients_server_interface(client_key):
        clientpeer = Peer.objects.filter(peer_interface__interface_key = client_key).first()
        return clientpeer.interface

    @staticmethod
    def get_by_id(interface_id: int) -> Interface | None:
        return Interface.objects.filter(id=interface_id).first()

    @staticmethod
    def get_by_key(interface_key: Key) -> Interface | None:
        return Interface.objects.filter(interface_key=interface_key).first()

    @staticmethod
    def get_by_name(name: str):
        return Interface.objects.filter(name=name)
    @staticmethod
    def get_client_interfaces_from_server(server_interface: Interface):
        peers = Peer.objects.filter(interface=server_interface).select_related("peer_interface")
        return [peer.peer_interface for peer in peers]

    @staticmethod
    def update_endpoint(interface: Interface, endpoint: str):
        interface.server_endpoint = endpoint
        interface.save(update_fields=['server_endpoint'])

    @staticmethod
    def update_port(interface: Interface, port: int):
        interface.listen_port = port
        interface.save(update_fields=['listen_port'])

    @staticmethod
    def update_ip_address(interface: Interface, ipaddress: str):
        interface.ip_address = ipaddress
        interface.save(update_fields=['ip_address'])

    @staticmethod
    def update_network(interface: Interface, ipnetwork: str, mask: str):
        interface.ip_network = ipnetwork
        interface.ip_network_mask = mask
        interface.save(update_fields=['ip_network', 'ip_network_mask'])

    @staticmethod
    def increment_session(interface: Interface):
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
    def get_peers_by_interface(interface: Interface):
        return Peer.objects.filter(interface=interface)

    @staticmethod
    def get_verified_peers_from_server(server_interface: Interface):
        return Peer.objects.filter(
            interface=server_interface,
            peer_interface__interface_key__user__profile__verified=True
        )

    @staticmethod
    def get_client_interface_peer(interface: Interface) -> Peer | None:
        return Peer.objects.filter(peer_interface=interface).first()

    @staticmethod
    def get_by_user(user: User):
        return Peer.objects.filter(peer_interface__interface_key__user=user)

    @staticmethod
    def get_server_interface_of_client(client_key: Key) -> Interface | None:
        client_peer = Peer.objects.filter(peer_interface__interface_key=client_key).first()
        return client_peer.interface if client_peer else None

    @staticmethod
    def get_ordered_snapshots(server_interface: Interface):
        return PeerSnapshot.objects.annotate(
            row_number=Window(
                expression=RowNumber(),
                partition_by=[F('peer')],
                order_by=F('collected_at').desc()
            )
        ).filter(peer__interface=server_interface)

    


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
    def get_by_id(user_id: int) -> User | None:
        return User.objects.filter(pk=user_id).first()

    @staticmethod
    def get_all_non_admin_users():
        return User.objects.exclude(is_superuser=True)

    @staticmethod
    def get_or_create_profile(user: User) -> Profile:
        profile, _ = Profile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def update_profile(profile: Profile, verified: bool = None, key_limit: int = None, key_count: int = None):
        """
        Updates fileds of the given profile based on the given parameter `verifyState`, `keyLimit`,`keyCount`.
        If a parameter of the field is None (default is None), it wont be updated.
        """
        fields = []
        if verified is not None:
            profile.verified = verified
            fields.append('verified')
        if key_limit is not None:
            profile.key_limit = key_limit
            fields.append('key_limit')
        if key_count is not None:
            profile.key_count = key_count
            fields.append('key_count')
        if fields:
            profile.save(update_fields=fields)

# --------------------------
# High-level Operations
# --------------------------
class ClientRepository:
    @staticmethod
    def save_client(client_key: Key, client_interface: Interface, server_peer: Peer):
        """Atomic save of client Key, Interface, and server Peer."""
        with transaction.atomic():
            KeyRepository.save(client_key)
            InterfaceRepository.save(client_interface)
            PeerRepository.save(server_peer)

    @staticmethod
    def delete_client(client_key: Key):
        """Deletes the client (cascades to interface and peers)."""
        KeyRepository.delete(client_key)


class ServerRepository:
    @staticmethod
    def save_server(server_key: Key, server_interface: Interface):
        with transaction.atomic():
            KeyRepository.save(server_key)
            InterfaceRepository.save(server_interface)

    @staticmethod
    def delete_server(server_key: Key):
        KeyRepository.delete(server_key)



