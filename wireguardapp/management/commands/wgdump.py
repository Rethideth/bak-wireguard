from django.core.management.base import BaseCommand
import subprocess
from datetime import datetime
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from wireguardapp.services.wireguard import saveWgDumpAll
import logging

logger = logging.getLogger('wg')

class Command(BaseCommand):
    help = "Ingest WireGuard status into Django models"

    
    def handle(self, *args, **options):
        saveWgDumpAll()
        self.stdout.write(self.style.SUCCESS("WireGuard ingestion completed"))

    
