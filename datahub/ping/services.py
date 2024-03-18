from django.db import DatabaseError

from datahub.company.models import Company
from datahub.core.queues.health_check import CheckRQWorkers


class CheckDatabase:
    """Check the database is up and running."""

    name = 'database'

    def check(self):
        """Perform the check."""
        try:
            Company.objects.all().exists()
            return True, ''
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase, CheckRQWorkers)
