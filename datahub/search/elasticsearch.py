import re

from django.conf import settings
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import Q

ES_INDEX = settings.ES_INDEX


def configure_connection():
    """Configure Elasticsearch default connection."""
    if settings.HEROKU:
        bonsai = settings.ES_HOST
        auth = re.search('https\:\/\/(.*)\@', bonsai).group(1).split(':')
        host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')

        connections.configure(
            default={
                'host': host,
                'port': settings.ES_PORT,
                'use_ssl': True,
                'http_auth': (auth[0], auth[1])
            }
        )
    else:
        connections.configure(
            default={
                'host': settings.ES_HOST,
                'port': settings.ES_PORT
            }
        )


def get_basic_search_query(term, entities=['company'], offset=0, limit=100):
    """Performs basic search looking for name and then _all in entity.

    Also returns number of results in other entities.
    """
    query = Q('multi_match', query=term, fields=['name', '_all'])
    s = Search(index=ES_INDEX).query(query)
    s = s.post_filter(
        Q('bool', should=[Q('term', _type=entity) for entity in entities])
    )

    s.aggs.bucket(
        'count_by_type', 'terms', field='_type'
    )

    return s[offset:offset + limit]


def get_search_by_entity_query(term=None, filters=None, entity=None, offset=0, limit=100):
    """Perform filtered search for given terms in given entity."""
    query = (
        Q('multi_match', query=term, fields=['name', '_all']),
        Q('term', _type=entity),
    )

    query_filter = []
    for k, v in filter(lambda f: '.' not in f[0], filters.items()):
        query_filter.append(Q('term', **{k: v}))

    # query nested fields
    for k, v in filter(lambda f: '.' in f[0], filters.items()):
        query_filter.append(
            Q('nested', path=k.split('.')[0],
              query=Q('term', **{k: v}))
        )

    s = Search(index=ES_INDEX).query('bool', must=query)
    s = s.post_filter('bool', must=query_filter)

    return s[offset:offset + limit]


def get_search_company_query(**kwargs):
    """Performs filtered search for company."""
    return get_search_by_entity_query(entity='company', **kwargs)


def get_search_contact_query(**kwargs):
    """Performs filtered search for contact."""
    return get_search_by_entity_query(entity='contact', **kwargs)


def bulk(actions=None, chunk_size=None, **kwargs):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(connections.get_connection(), actions=actions, chunk_size=chunk_size, **kwargs)


def legacy_search_by_term_query(term, doc_type=None, offset=0, limit=100):
    """Searches for term in the index."""
    if doc_type:
        q = Search(index=ES_INDEX).filter(
            'multi_match', query=term, fields=['name^3', 'alias^3', '*_name', '*_postcode']
        )
        q = q.query('bool', filter=[Q('terms', _type=doc_type)])

    else:
        q = Search(index=ES_INDEX).query(Q(
            'multi_match', query=term, fields=['name^3', 'alias^3', '*_name', '*_postcode']
        ))

    return q[offset:offset + limit]


def document_exists(client, doc_type, document_id):
    """Check whether the document with a specific ID exists."""
    return client.exists(
        index=ES_INDEX,
        doc_type=doc_type,
        id=document_id,
        realtime=True
    )


def remap_fields(filter):
    """Replaces fields to match Elasticsearch data model."""
    name_map = {
        'sector': 'sector.id',
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'uk_region': 'uk_region.id',
        'trading_address_country': 'trading_address_country.id',
        'advisor': 'advisor.id',
    }
    return dict(zip(map(lambda x: name_map.get(x, x), filter.keys()), filter.values()))
