from django.db import DatabaseError
from elasticsearch import ElasticsearchException
from rest_framework import status

from datahub.company.models import Company
from datahub.es.connector import ESConnector
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


class CheckElasticsearch:
    """Check Elastic Search is up and running."""

    name = 'elasticsearch'

    def check(self):
        """Perform the check."""
        try:
            connector = ESConnector()
            connector.ping()
            return True, ''
        except ElasticsearchException as e:
            return False, e


services_to_check = (CheckDatabase, CheckElasticsearch)
