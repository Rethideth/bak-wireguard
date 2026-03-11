import logging
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from collections import defaultdict

from wireguardapp.models import Interface, Peer, Key, Profile

from .wireguardcmd import  generateKeyPair
from .crypto import encrypt_value

import ipaddress
import re

from wireguardapp.database.repository import InterfaceRepository



logger = logging.getLogger("wg")

KEEPALIVE = 25
PORT = 51820



# -----------------------------
# Model Creation Functions
# -----------------------------
class ModelFactory:
    # -------------------
    # IP Allocation
    # -------------------
    @staticmethod
    def allocate_ip_address(server_interface: Interface) -> str:
        if server_interface.interface_type != Interface.SERVER:
            raise TypeError("Interface není typy server.")

        network = ipaddress.ip_network(f"{server_interface.ip_network}/{server_interface.ip_network_mask}")
        clients = InterfaceRepository.get_client_interfaces_from_server(server_interface)
        occupied = {ipaddress.IPv4Address(i.ip_address) for i in clients}
        occupied.add(ipaddress.IPv4Address(server_interface.ip_address))

        for ip in network.hosts():
            if ip not in occupied:
                return str(ip)

        raise ValueError("Nejsou žádné volné ip adresy pro server.")
    @staticmethod
    def create_key(user: User, name: str = None) -> Key:
        private_key, public_key = generateKeyPair()
        return Key(
            user=user,
            private_key=encrypt_value(private_key),
            public_key=public_key,
            name=name
        )

    @staticmethod
    def create_client_interface(user: User, key: Key, server_interface: Interface) -> Interface:
        interface_name = f"{user.username}-{timezone.datetime.now().strftime('%Y%m%d%H%M%S')}"
        ip_address = ModelFactory.allocate_ip_address(server_interface)
        return Interface(
            name=interface_name,
            interface_key=key,
            ip_address=ip_address,
            ip_network_mask=32,
            interface_type=Interface.CLIENT
        )

    @staticmethod
    def create_server_interface(key: Key, ip_network: str, netmask: str, endpoint: str, port: str) -> Interface:
        network = ipaddress.ip_network(f"{ip_network}/{netmask}")
        address = next(network.hosts())
        name = ModelFactory.make_server_new_name()
        return Interface(
            name=name,
            interface_key=key,
            ip_network=ip_network,
            ip_network_mask=netmask,
            ip_address=address,
            interface_type=Interface.SERVER,
            server_endpoint=endpoint,
            listen_port=port
        )

    @staticmethod
    def create_server_peer(server_interface: Interface, client_interface: Interface) -> Peer:
        return Peer(
            interface=server_interface,
            peer_interface=client_interface,
            persistent_keepalive=KEEPALIVE
        )

    @staticmethod
    def create_profile(user: User) -> Profile:
        return Profile(user=user, verified=False)

    @staticmethod
    def make_server_new_name() -> str:
        names = Interface.objects.filter(interface_type=Interface.SERVER).values_list("name", flat=True)
        nums = [int(re.search(r"\d+", x).group()) for x in names if re.search(r"\d+", x)]
        num = max(nums, default=-1)
        return f"wg-server{num + 1}"