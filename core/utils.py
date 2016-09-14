"""Core utils"""

from django.conf import settings

from elasticsearch import Elasticsearch


def get_elasticsearch_client():
    """Return an istance of the elasticsearch client or similar."""
    return Elasticsearch([{
        'host': settings.ES_HOST,
        'port': settings.ES_PORT
    }])

