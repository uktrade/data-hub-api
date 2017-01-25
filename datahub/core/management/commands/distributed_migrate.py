import os
import redis
import redis_lock
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import transaction


class Command(MigrateCommand):
    """Updates database schema. Manages both apps with migrations and those without."""

    def handle(self, *args, **options):
        """Execute command."""
        conn = redis.StrictRedis.from_url(os.environ.get('REDIS_URL', 'redis://redis'))
        with redis_lock.Lock(conn, 'migrations-run'):
            with transaction.atomic():
                super().handle(*args, **options)
