from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "My custom management command"

    def handle(self, *args, **options):
        self.stdout.write("Hello from my command!")