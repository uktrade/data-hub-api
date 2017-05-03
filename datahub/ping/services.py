from django.db import DatabaseError

from datahub.company.models import Company


class CheckDatabase:
    """Check the database is up and running."""

    name = 'database'

    def check(self):
        """Perform the check."""
        try:
            Company.objects.all().count()
            return True, ''
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase, )
