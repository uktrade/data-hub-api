from django.conf import settings
from django.db import DatabaseError

from datahub.company.models import Company
from datahub.es.connector import ESConnector
from datahub.korben.connector import KorbenConnector


def check_database():
    """Check the database is up and running."""
    try:
        Company.objects.all().count()
        return True
    except DatabaseError as e:
        return False


def check_elasticsearch():
    """Check Elastic Search is up and running."""
    connector = ESConnector()


def check_korben():
    connector = KorbenConnector()
    connector.ping()


checks = (check_database, check_elasticsearch, check_korben)
