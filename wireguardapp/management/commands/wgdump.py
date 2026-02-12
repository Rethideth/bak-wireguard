from django.core.management.base import BaseCommand
import subprocess
from datetime import datetime
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
import logging


class Command(BaseCommand):
    help = "Ingest WireGuard status into Django models"

    def get_wg_dump(self):
        """Run 'wg show all dump' and return lines"""
        result = subprocess.run(
            ["wg", "show", "all", "dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().splitlines()

    def handle(self, *args, **options):
        lines = self.get_wg_dump()
        i = 0

        while i < len(lines):
            # Interface line
            parts = lines[i].split()
            iface_name, _private_key, public_key, listen_port, fwmark = parts
            # Get user by key
            key = Key.objects.get(
                public_key = public_key
            )

            interface, _ = Interface.objects.get_or_create(
                name=iface_name,
                defaults={
                    "interface_key": key,
                    "listen_port": int(listen_port),
                    "fwmark": fwmark if fwmark != "off" else None,
                },
            )
            # Update listen_port/fwmark if changed
            Interface.objects.filter(pk=interface.pk).update(
                listen_port=int(listen_port),
                fwmark=None if fwmark == "off" else fwmark,
            )

            i += 1

            # Peer lines
            while i < len(lines) and lines[i].startswith(iface_name):
                (
                    iface,
                    public_key,
                    preshared_key,
                    endpoint,
                    allowed_ips,
                    latest_handshake,
                    rx_bytes,
                    tx_bytes,
                    keepalive,
                ) = lines[i].split()

                key = Key.objects.get(
                    public_key = public_key
                )

                peer, _ = Peer.objects.get_or_create(
                    interface=interface,
                    peer_key=key,
                    defaults={
                        "persistent_keepalive": None if keepalive == "off" else int(keepalive),
                    },
                )
                # Update keepalive if changed
                Peer.objects.filter(pk=peer.pk).update(
                    persistent_keepalive=None if keepalive == "off" else int(keepalive)
                )



                # Insert snapshot
                handshake_dt = None if latest_handshake == "0" else datetime.fromtimestamp(int(latest_handshake))
                PeerSnapshot.objects.create(
                    peer=peer,
                    endpoint=None if endpoint == "(none)" else endpoint,
                    latest_handshake=handshake_dt,
                    rx_bytes=int(rx_bytes),
                    tx_bytes=int(tx_bytes),
                )

                i += 1

        self.stdout.write(self.style.SUCCESS("WireGuard ingestion completed"))

    
