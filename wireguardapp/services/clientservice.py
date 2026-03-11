import logging
from django.contrib.auth.models import User
from wireguardapp.models import Interface, Key, Profile
from wireguardapp.database.repository import InterfaceRepository,PeerRepository,UserRepository,KeyRepository,ClientRepository
from .wireguardcmd import addWGPeer, removeWGPeer, generateClientConfText
from .modelfactory import ModelFactory

logger = logging.getLogger("wg")


class ClientService:
    # -------------------
    # Key & Interface Access
    # -------------------
    @staticmethod
    def get_key_by_id(key_id: int) -> Key | None:
        return KeyRepository.get_by_id(key_id=key_id)

    @staticmethod
    def get_clients_server_interface(client_key: Key) -> Interface | None:
        return InterfaceRepository.get_clients_server_interface(client_key)

    @staticmethod
    def get_user_profile(user: User) -> Profile:
        return UserRepository.get_or_create_profile(user=user)

    @staticmethod
    def get_user_keys(user: User):
        return KeyRepository.get_by_user(user)

    @staticmethod
    def check_user_of_key(user: User, key: Key) -> bool:
        return key.user == user or user.is_superuser or user.is_staff
    
    @staticmethod
    def change_key_name(key:Key, name : str):
        return KeyRepository.update_name(key,name)

    # -------------------
    # Client Creation
    # -------------------
    @staticmethod
    def create_new_client(user: User, name: str, server_interface: Interface) -> str | None:
        profile = ClientService.get_user_profile(user)
        if profile.key_limit <= profile.key_count:
            return "Dosáhli jste maximum počet klíču, co můžete mít."

        try:
            key = ModelFactory.create_key(user, name)
            interface = ModelFactory.create_client_interface(user, key, server_interface)
            server_peer = ModelFactory.create_server_peer(server_interface, interface)
        except TypeError as e:
            return "Rozhraní pro alokaci ip adresy není typu server. " + str(e)
        except ValueError:
            return "Volné ip adresy pro tento server byly vyčerpány."
        except Exception:
            return "Nastala chyba při vytváření klienta."

        # Save all client models atomically
        ClientRepository.save_client(client_key=key, client_interface=interface, server_peer=server_peer)
        UserRepository.update_profile(profile=profile, key_count=profile.key_count+1)

        # Add peer to WireGuard if user is verified
        if profile.verified:
            try:
                addWGPeer(
                    serverInterfaceName=server_interface.name,
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
    def remove_client(user: User, key: Key) -> str | None:
        profile = ClientService.get_user_profile(user)
        if not profile.verified:
            return "Nejste ověřeni, kontaktujte správce pro ověření"

        server_interface = InterfaceRepository.get_clients_server_interface(key)
        ClientRepository.delete_client(key)
        UserRepository.update_profile(profile=profile, key_count=profile.key_count -1)

        # Remove from WireGuard
        try:
            removeWGPeer(
                serverInterfaceName=server_interface.name,
                peerKey=key.public_key
            )
        except RuntimeError as e:
            pass

        return None

    # -------------------
    # WireGuard Configuration
    # -------------------
    @staticmethod
    def generate_client_conf(user: User, key: Key, only_vpn: bool = False) -> str:
        profile = ClientService.get_user_profile(user)
        if not profile.verified:
            return "Nejste ověřeni, kontaktujte správce pro ověření"
        
        client_interface = InterfaceRepository.get_by_key(key)
        if client_interface.interface_type == Interface.SERVER:
            return "Pro server nemůže být vrácená konfigurace."
        
        server_peer = PeerRepository.get_client_interface_peer(client_interface)
        

        if only_vpn:
            allowed_ips = f"{server_peer.interface.ip_network}/{server_peer.interface.ip_network_mask}"
            return generateClientConfText(
                clientInterface=client_interface,
                serverPeer=server_peer,
                endpoint=server_peer.interface.server_endpoint,
                listenPort=server_peer.interface.listen_port,
                allowedIPs=allowed_ips
            )
        else:
            return generateClientConfText(
                clientInterface=client_interface,
                serverPeer=server_peer,
                endpoint=server_peer.interface.server_endpoint,
                listenPort=server_peer.interface.listen_port
            )

    # -------------------
    # User Management
    # -------------------
    @staticmethod
    def create_user(form) -> User:
        """
        Creates a new user and its profile
        """
        user = form.save(commit=False)
        profile = ModelFactory.create_profile(user)
        UserRepository.save(user=user,profile=profile)
        form.save_m2m()
        return user

    @staticmethod
    def get_user_from_id(user_id: int) -> User | None:
        return UserRepository.get_by_id(user_id=user_id)