from collections import defaultdict
from urllib.parse import ParseResult, urlparse  # noqa: F401

import dateutil.parser
from django.conf import settings
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import Match, MatchPhrase, Q


def configure_connection():
    """Configure Elasticsearch default connection."""
    connections.configure(
        default={
            'hosts': [settings.ES_URL]
        }
    )


def get_search_term_query(term):
    """Returns search term query."""
    return Q('bool', should=[
        MatchPhrase(name={'query': term, 'boost': 2}),
        MatchPhrase(_all={'query': term, 'boost': 1.5}),
        Match(name={'query': term, 'boost': 1.0}),
        Match(_all={'query': term, 'boost': 0.5}),
    ])


def get_basic_search_query(term, entities=('company',), offset=0, limit=100):
    """Performs basic search looking for name and then _all in entity.

    Also returns number of results in other entities.
    """
    query = get_search_term_query(term)
    s = Search(index=settings.ES_INDEX).query(query)
    s = s.post_filter(
        Q('bool', should=[Q('term', _type=entity) for entity in entities])
    )

    s.aggs.bucket(
        'count_by_type', 'terms', field='_type'
    )

    return s[offset:offset + limit]


def get_search_by_entity_query(term=None, filters=None, entity=None, ranges=None, offset=0, limit=100):
    """Perform filtered search for given terms in given entity."""
    query = [Q('term', _type=entity)]
    if term != '':
        query.append(get_search_term_query(term))

    query_filter = []

    if filters:
        for k, v in filters.items():
            term = Q('term', **{k: v})
            if '.' not in k:
                query_filter.append(term)
            else:
                # query nested fields
                query_filter.append(
                    Q('nested', path=k.split('.')[0], query=term)
                )

    if ranges:
        for k, v in ranges.items():
            query_filter.append(
                Q('range', **{k: v})
            )

    s = Search(index=settings.ES_INDEX).query('bool', must=query)
    s = s.post_filter('bool', must=query_filter)

    return s[offset:offset + limit]


def get_search_company_query(**kwargs):
    """Performs filtered search for company."""
    return get_search_by_entity_query(entity='company', **kwargs)


def get_search_contact_query(**kwargs):
    """Performs filtered search for contact."""
    return get_search_by_entity_query(entity='contact', **kwargs)


def get_search_investment_project_query(**kwargs):
    """Performs filtered search for investment project."""
    return get_search_by_entity_query(entity='investment_project', **kwargs)


def bulk(actions=None, chunk_size=None, **kwargs):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(connections.get_connection(), actions=actions, chunk_size=chunk_size, **kwargs)


def remap_fields(fields):
    """Replaces fields to match Elasticsearch data model."""
    name_map = {
        'sector': 'sector.id',
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'uk_region': 'uk_region.id',
        'trading_address_country': 'trading_address_country.id',
        'adviser': 'adviser.id',
        'client_relationship_manager': 'client_relationship_manager.id',
        'investor_company': 'investor_company.id',
        'investment_type': 'investment_type.id',
        'phase': 'phase.id',
    }
    return {name_map.get(k, k): v for k, v in fields.items()}


def date_range_fields(fields):
    """Finds and format range fields."""
    filters = {}
    ranges = defaultdict(dict)

    for k, v in fields.items():
        if k.endswith('_before') or k.endswith('_after'):
            range_key = k[:k.rindex('_')]

            if k.endswith('_before'):
                ranges[range_key]['lte'] = dateutil.parser.parse(fields[k])
            if k.endswith('_after'):
                ranges[range_key]['gte'] = dateutil.parser.parse(fields[k])

            continue

        filters.update({k: v})

    return filters, ranges
