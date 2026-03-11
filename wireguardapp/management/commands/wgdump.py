from django.core.management.base import BaseCommand
import subprocess
from datetime import datetime
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from wireguardapp.services.wireguardcmd import saveWgDumpAll
import logging
import datetime

logger = logging.getLogger('wg')

class Command(BaseCommand):
    help = "Ingest WireGuard status into Django models"

    
    def handle(self, *args, **options):
        saveWgDumpAll()
        logger.info(f"({datetime.datetime.now()}): WireGuard peer state aggregation completed")
        self.stdout.write(self.style.SUCCESS("WireGuard ingestion completed"))

    
