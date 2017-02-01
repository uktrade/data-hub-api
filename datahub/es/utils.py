"""Core utils."""
import re

from django.conf import settings

from elasticsearch import Elasticsearch


def get_elasticsearch_client():
    """Return an instance of the elasticsearch client or similar."""
    if settings.HEROKU:
        bonsai = settings.ES_HOST
        auth = re.search('https\:\/\/(.*)\@', bonsai).group(1).split(':')
        host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')

        # Connect to cluster over SSL using auth for best security:
        es_header = [{
            'host': host,
            'port': settings.ES_PORT,
            'use_ssl': True,
            'http_auth': (auth[0], auth[1])
        }]
        return Elasticsearch(es_header)
    else:
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


def document_exists(client, doc_type, document_id):
    """Check whether the document with a specific ID exists."""
    return client.exists(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        id=document_id,
        realtime=True)
