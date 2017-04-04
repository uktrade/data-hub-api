from django.db import DatabaseError
from rest_framework import status

from datahub.company.models import Company
from datahub.korben.connector import KorbenConnector


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


class CheckKorben:
    """Get status from Korben."""

    name = 'korben'

    def check(self):
        """Get status from Korben."""
        connector = KorbenConnector()
        response = connector.ping()
        if response and response.status_code == status.HTTP_200_OK:
            return True, ''
        else:
            return False, response.content if response else 'Unknown error'


services_to_check = (CheckDatabase, CheckKorben)
