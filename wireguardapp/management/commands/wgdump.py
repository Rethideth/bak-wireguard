from django.core.management.base import BaseCommand
import subprocess
from datetime import datetime
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from wireguardapp.services.server import getServerInterface 
import logging


class Command(BaseCommand):
    help = "Ingest WireGuard status into Django models"

    def get_wg_dump(self):
        """Run 'wg show <server_interface> dump' and return lines"""
        server = getServerInterface()
        result = subprocess.run(
            ["wg", "show", server.name , "dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().splitlines()

    def handle(self, *args, **options):
        lines = self.get_wg_dump()
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
 
            peer = Peer.objects.get(peer_key__public_key = public_key)
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

    
