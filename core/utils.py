"""Core utils"""

from django.conf import settings

from elasticsearch import Elasticsearch


def get_elasticsearch_client():
    """Return an instance of the elasticsearch client or similar."""
    return Elasticsearch([{
        'host': settings.ES_HOST,
        'port': settings.ES_PORT
    }])


def format_es_results(hits):
    """ES results are contained in a list of dictionaries.

    The key _source contains the actual data, we want to expose that to the upper level.
    In this way the data set can be directly returned by the view.
    """
    results = []
    for hit in hits:
        result = {
            'type': hit['_type'],
            'id': hit['_id'],
        }
        result.update(hit['_source'])
        results.append(result)

    return results
