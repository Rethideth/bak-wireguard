from django.core.management.base import BaseCommand
import subprocess
from datetime import datetime
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from wireguardapp.services.server import selectAllServerInterfaces
import logging


class Command(BaseCommand):
    help = "Ingest WireGuard status into Django models"

    def get_wg_dump(self, interface : Interface):
        """Run 'wg show <server_interface> dump' and return lines"""
        result = subprocess.run(
            ["wg", "show", interface.name , "dump"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().splitlines()

    def handle(self, *args, **options):
        interfaces = selectAllServerInterfaces()

        for interface in interfaces:
            try:
                lines = self.get_wg_dump(interface=interface)
            except:
                continue
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

                # Insert snapshot
                handshake_dt = None if latest_handshake == "0" else datetime.fromtimestamp(int(latest_handshake))
                PeerSnapshot.objects.create(
                    peer=peer,
                    endpoint=None if endpoint == "(none)" else endpoint,
                    latest_handshake=handshake_dt,
                    rx_bytes=int(rx_bytes),
                    tx_bytes=int(tx_bytes),
                    session=interface.session_number
                )
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

                peer.total_rx_bytes = diffR
                peer.total_tx_bytes = diffT
                peer.last_rx_bytes = currentRx
                peer.last_tx_bytes = currentTx

                peer.save(update_fields=
                        ['total_rx_bytes',
                         'total_tx_bytes',
                         'last_rx_bytes',
                         'last_tx_bytes'])

                i += 1
                self.stdout.write(self.style.SUCCESS(f"WireGuard saved state of {interface.name} - {peer.peer_key}"))

        self.stdout.write(self.style.SUCCESS("WireGuard ingestion completed"))

    
