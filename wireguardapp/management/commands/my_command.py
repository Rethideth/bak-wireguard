from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = "Test command"

    def handle(self, *args, **options):
        
        serverInterfaceName = 'wg-server'
        peerKey = 'B5L3cSXODu237hSD6uIBlV5lFHJxUw0wMqMM/X53CwQ='
        ipAddress = '10.10.0.10/32'
        try:
            result = subprocess.run(
                [
                    "/var/www/bakproject/scripts/enablepeer.sh", 
                    serverInterfaceName, peerKey,ipAddress
                ],
                check=True,

            )
        except PermissionError as e:
            print("Permission denied")
        except subprocess.CalledProcessError as e:
            print("Cannot add a new peer")
            print("stderr:", e.stderr)
            print("stdout:",e.stdout)


        return 0