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
from wireguardapp.database.repository import InterfaceRepository,PeerRepository,UserRepository,KeyRepository,ServerRepository

logger = logging.getLogger("wg")


class ServerService:
    # -------------------
    # Server Interface Getters
    # -------------------
    @staticmethod
    def get_first_server_interface() -> Interface | None:
        return InterfaceRepository.get_first_server_interface()

    @staticmethod
    def get_server_interface_by_id(interface_id: int) -> Interface | None:
        return InterfaceRepository.get_by_id(interface_id=interface_id)

    @staticmethod
    def get_all_server_interfaces():
        return InterfaceRepository.get_all_server_interfaces()

    # -------------------
    # WireGuard Control
    # -------------------
    @staticmethod
    def start_server(server_interface: Interface, interface_internet_name: str):
        InterfaceRepository.increment_session(interface=server_interface)
        result = startWGserver(server_interface, interface_internet_name)
        saveWgDump(server_interface)
        return result

    @staticmethod
    def stop_server(server_interface: Interface):
        return stopWGserver(server_interface)

    @staticmethod
    def check_server(server_interface: Interface):
        return isWGserverUp(server_interface)

    # -------------------
    # Server Creation / Removal
    # -------------------
    @staticmethod
    def create_new_server(name: str, ip_network: str, network_mask: str, endpoint: str, port: str, client_to_client : bool) -> str | None:
        try:
            key = ModelFactory.create_key(user=None, name=name)
            interface = ModelFactory.create_server_interface(key, ip_network, network_mask, endpoint, port,client_to_client)
        except ValueError:
            return "Hodnoty nového server rozhraní nejsou validní."
        except Exception:
            return "Selhalo vytváření nového rozhraní serveru."
        ServerRepository.save_server(key,interface)
        return None

    @staticmethod
    def remove_server(server_interface: Interface):
        ServerService.stop_server(server_interface)
        ServerRepository.delete_server(server_interface.interface_key)

    # -------------------
    # Peer Management
    # -------------------
    @staticmethod
    def get_server_interface_peers(server_interface: Interface):
        return PeerRepository.get_peers_by_interface(server_interface)

    @staticmethod
    def get_wg_peer_connection_state(server_interface: Interface):
        return getWGPeersState(server_interface)

    @staticmethod
    def get_interface_peers_total_bytes(server_interface: Interface) -> list[dict]:
        peers = ServerService.get_server_interface_peers(server_interface)
        ranked = PeerRepository.get_ordered_snapshots_from_interface(server_interface)
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
    def get_network_interfaces():
        return selectAllNetworkInterfaces()

    # -------------------
    # User Management
    # -------------------
    @staticmethod
    def get_all_client_users():
        return UserRepository.get_all_non_admin_users()

    @staticmethod
    def switch_verify_profile(user_id: int) -> Profile:
        user = UserRepository.get_by_id(user_id)
        profile = UserRepository.get_or_create_profile(user)

        if profile.verified:
            UserRepository.update_profile(profile, verified=False)
            ServerService.disconnect_user_from_wg(user)
        else:
            UserRepository.update_profile(profile, verified=True)
            ServerService.connect_user_to_wg(user)

        return UserRepository.get_or_create_profile(user)

    @staticmethod
    def connect_user_to_wg(user: User):
        peers = PeerRepository.get_by_user(user)
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
    def disconnect_user_from_wg(user: User):
        peers = PeerRepository.get_by_user(user)
        for peer in peers:
            try:
                removeWGPeer(
                    serverInterfaceName=peer.interface.name,
                    peerKey=peer.peer_interface.interface_key.public_key
                )
            except Exception as e:
                logger.warning(f"Failed to disconnect user peer: {e}")

    @staticmethod
    def remove_user(user_id: int) -> str | None:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return "Uživatel nenalezen"

        ServerService.disconnect_user_from_wg(user)
        UserRepository.delete(user)
        return None

    # -------------------
    # Server Update
    # -------------------
    @staticmethod
    def update_server(interface: Interface, changed: list[str]):
        try:
            with transaction.atomic():
                if "ip_network" in changed or "ip_network_mask" in changed:
                    ServerService.update_server_peers_ip_addresses(interface)
                if "server_endpoint" in changed:
                    InterfaceRepository.update_endpoint(interface,interface.server_endpoint)
                if "listen_port" in changed:
                    InterfaceRepository.update_port(interface, interface.listen_port)
                if "client_to_client" in changed:
                    InterfaceRepository.update_client_to_client(interface,interface.client_to_client)
        except ValueError as e:
            return str(e)
        except Exception:
            return "Nastala chyba při aktualizaci serveru"

    @staticmethod
    def update_server_peers_ip_addresses(server_interface: Interface):
        network = ipaddress.ip_network(f"{server_interface.ip_network}/{server_interface.ip_network_mask}")
        logger.info(f"network: {network}")
        
        clients = InterfaceRepository.get_client_interfaces_from_server(server_interface)
        count = network.num_addresses - 2
        if count < len(clients) + 1:
            raise ValueError("Velikost sítě není dostačující pro všechny klienty")

        InterfaceRepository.update_network(server_interface, server_interface.ip_network, server_interface.ip_network_mask)

        hosts = network.hosts()
        InterfaceRepository.update_ip_address(server_interface,next(hosts))
        for client in clients:
            InterfaceRepository.update_ip_address(client,next(hosts))