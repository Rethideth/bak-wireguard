from django.core.management.base import BaseCommand
import subprocess
from django.contrib.auth.models import User
import time


class Command(BaseCommand):
    help = "Test command"

    def handle(self, *args, **options):
        pass

