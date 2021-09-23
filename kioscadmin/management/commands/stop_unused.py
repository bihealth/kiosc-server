"""Django command for stopping unused containers."""

from django.core.management.base import BaseCommand
from django.db import transaction

from kioscadmin.tasks import stop_inactive_containers


class Command(BaseCommand):
    """Implementation for stopping unused containers."""

    #: Help message displayed on the command line.
    help = "Stop containers that haven't been accessed via proxy for a defined time period."

    @transaction.atomic
    def handle(self, *args, **options):
        """Perform stopping unused containers."""

        msgs = stop_inactive_containers()
        msg_fin = "Command successfully finished"

        for msg in msgs:
            self.stdout.write(self.style.NOTICE(msg))

        self.stdout.write(self.style.SUCCESS(msg_fin))
