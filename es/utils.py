"""Core utils"""

from django.conf import settings

from elasticsearch import Elasticsearch


def get_elasticsearch_client():
    """Return an instance of the elasticsearch client or similar."""
    return Elasticsearch([{
        'host': settings.ES_HOST,
        'port': settings.ES_PORT
    }])


def format_es_results(es_results):
    """Make the results JSON serializable."""

    results = {
        'total': es_results.hits.total,
        'max_score': es_results.hits.max_score,
        'hits': es_results.hits.hits,
    }

    return results

