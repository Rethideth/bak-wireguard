from django.core.management.base import BaseCommand
import subprocess
import tempfile
from wireguardapp.services.wireguardcmd import stopWGserver
from django.conf import settings
import logging

logger = logging.getLogger('wg')

class Command(BaseCommand):
    help = "Stops wireguard server interface"

    def handle(self, *args, **options):
        stopWGserver()
        return 

        




        