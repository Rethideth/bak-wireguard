from django.core.management.base import BaseCommand
import subprocess
import tempfile
from wireguardapp.services.wireguard import startWGserver
from django.conf import settings
import logging

logger = logging.getLogger('wg')

class Command(BaseCommand):
    help = "Update or start wireguard server interface"

    def handle(self, *args, **options):
        startWGserver()
        return 

        




        