from django.core.management.base import BaseCommand
import subprocess
from wireguardapp.services.server import getServerInterface
from django.contrib.auth.models import User
import time


class Command(BaseCommand):
    help = "Test command"

    def handle(self, *args, **options):
        interface = getServerInterface()
        now = int(time.time())

        try:
            result = subprocess.run(
                ["wg", "show", interface.name, "dump"],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split("\n")

            peers = []

            # First line is interface info → skip it
            for line in lines[1:]:
                parts = line.split("\t")

                public_key = parts[0]
                endpoint = parts[2]
                latest_handshake = int(parts[4])
                transfer_rx = int(parts[5])
                transfer_tx = int(parts[6])
                is_connected = (
                    latest_handshake > 0 and
                    (now - latest_handshake) < 120
                )

                peers.append({
                    "public_key": public_key[:12] + "...",
                    "endpoint": endpoint or "—",
                    "handshake": latest_handshake,
                    "rx": transfer_rx,
                    "tx": transfer_tx,
                    'is_connected':is_connected
                })

            return print(peers)

        except Exception:
            return print('nok')

