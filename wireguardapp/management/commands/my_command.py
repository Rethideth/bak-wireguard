from django.core.management.base import BaseCommand
import subprocess
from wireguardapp.services.server import getFirstServerInterface,getServerInterfacePeers,getInterfacePeersTotalBytes
from django.contrib.auth.models import User
import time


class Command(BaseCommand):
    help = "Test command"

    def handle(self, *args, **options):
        interface = getFirstServerInterface()
        print(getServerInterfacePeers(interface))
        print(getInterfacePeersTotalBytes(interface))

