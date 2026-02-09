from django.core.management.base import BaseCommand
import subprocess
import tempfile
from wireguardapp.service.wireguard import generateServerConfText
from django.conf import settings
import logging

logger = logging.getLogger('wg')

class Command(BaseCommand):
    help = "Update or start wireguard server interface"

    def handle(self, *args, **options):
        conf, servername = generateServerConfText()

        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False, 
            prefix='wg-',
            suffix='.conf') as temp:
            temp.write(conf)
            tmpPath = temp.name


        cmd = [
            "sudo",
            settings.BASE_DIR / "scripts/wg-start.sh", 
            tmpPath,
            servername
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print('error: ' + e.stderr)

        return 

        




        