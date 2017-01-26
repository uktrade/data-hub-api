from django.core.management.commands.migrate import Command as MigrateCommand
from django_pglocks import advisory_lock


class Command(MigrateCommand):
    """Updates database schema. Manages both apps with migrations and those without."""

    def handle(self, *args, **options):
        """Execute command."""
        with advisory_lock('migrations'):
            super().handle(*args, **options)
