from collections import defaultdict
from itertools import chain

import dateutil.parser
from django.conf import settings
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch_dsl import analysis, Index, Search
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.query import Match, MatchPhrase, Q

from .apps import get_search_apps


lowercase_keyword_analyzer = analysis.CustomAnalyzer(
    'lowercase_keyword_analyzer',
    tokenizer='keyword',
    filter=('lowercase',)
)

# Trigram tokenizer enables us to support partial matching
trigram = analysis.tokenizer('trigram', 'nGram', min_gram=3, max_gram=3)

# Filters out "-" so that t-shirt and tshirt can be matched
special_chars = analysis.char_filter('special_chars', 'mapping', mappings=('-=>',))
trigram_analyzer = analysis.CustomAnalyzer(
    'trigram_analyzer',
    tokenizer=trigram,
    char_filter=special_chars,
    filter=('lowercase',),
)


def configure_connection():
    """Configure Elasticsearch default connection."""
    connections.configure(
        default={
            'hosts': [settings.ES_URL]
        }
    )


def configure_index(index_name, settings=None):
    """Configures Elasticsearch index."""
    client = connections.get_connection()
    if not client.indices.exists(index=index_name):
        index = Index(index_name)
        index.analyzer(lowercase_keyword_analyzer)
        index.analyzer(trigram_analyzer)
        if settings:
            index.settings(**settings)
        index.create()


def get_search_term_query(term, fields=None):
    """Returns search term query."""
    if term == '':
        return Q('match_all')

    should_query = [
        # Promote exact name match
        MatchPhrase(name_keyword={'query': term, 'boost': 2}),
        # Exact match by id
        MatchPhrase(id={'query': term}),
        # Match similar name
        Match(name={'query': term}),
        # Partial match name
        MatchPhrase(name_trigram={'query': term}),
    ]

    if fields:
        should_query.extend([get_match_query(field, term) for field in fields])

    return Q('bool', should=should_query)


def remap_sort_field(field):
    """Replaces fields to aliases suitable for sorting."""
    name_map = {
        'name': 'name_keyword',
    }
    return name_map.get(field, field)


def get_sort_query(qs, field_order=None):
    """Attaches sort query."""
    if field_order is None:
        return qs

    tokens = field_order.rsplit(':', maxsplit=1)
    order = tokens[1] if len(tokens) > 1 else 'asc'

    sort_params = {
        'order': order,
        'missing': '_first' if order == 'asc' else '_last'
    }

    # check if we sort by field in nested document (example: 'stage.name')
    if '.' in tokens[0]:
        # extract and add path to nested document (example: 'stage')
        sort_params['nested_path'] = tokens[0].split('.', 1)[0]

    qs = qs.sort({
        remap_sort_field(tokens[0]): sort_params
    })
    return qs


def get_basic_search_query(term, entities=None, field_order=None, offset=0, limit=100):
    """Performs basic search looking for name and then SEARCH_FIELDS in entity.

    Also returns number of results in other entities.
    """
    all_models = (search_app.ESModel for search_app in get_search_apps())
    fields = set(chain.from_iterable(entity.SEARCH_FIELDS for entity in all_models))

    # Sort the fields so that this function is deterministic
    # and the same query is always generated with the same inputs
    fields = sorted(fields)

    query = get_search_term_query(term, fields=fields)
    s = Search(index=settings.ES_INDEX).query(query)
    s = s.post_filter(
        Q('bool', should=[Q('term', _type=entity._doc_type.name) for entity in entities])
    )

    s = get_sort_query(s, field_order=field_order)
    s.aggs.bucket(
        'count_by_type', 'terms', field='_type'
    )

    return s[offset:offset + limit]


def get_term_query(field, value):
    """Gets term query."""
    term = Q('term', **{field: value})
    if '.' not in field:
        return term

    return Q('nested', path=field.split('.', maxsplit=1)[0], query=term)


def get_match_query(field, value):
    """Gets match query."""
    match = Q('match', **{field: value})
    if '.' not in field:
        return match

    return Q('nested', path=field.split('.', maxsplit=1)[0], query=Q('bool', must=match))


def apply_aggs_query(search, aggs):
    """Applies aggregates query to the search."""
    for agg in aggs:
        # skip range filters as we can't aggregate them
        if any(agg.endswith(x) for x in ('_before', '_after')):
            continue
        agg = remap_filter_id_field(agg)

        search_aggs = search.aggs
        if '.' in agg:
            search_aggs = search_aggs.bucket(
                agg,
                'nested',
                path=agg.split('.', 1)[0]
            )

        search_aggs.bucket(agg, 'terms', field=agg)


def get_search_by_entity_query(term=None,
                               filters=None,
                               entity=None,
                               ranges=None,
                               field_order=None,
                               aggs=None,
                               offset=0,
                               limit=100):
    """Perform filtered search for given terms in given entity."""
    query = [Q('term', _type=entity._doc_type.name)]
    if term != '':
        query.append(get_search_term_query(term, fields=entity.SEARCH_FIELDS))

    # document must match all filters in the list (and)
    must_filter = []

    if filters:
        for k, v in filters.items():
            if isinstance(v, list):
                # perform "or" query
                must_filter.append(
                    Q('bool',
                      should=[get_term_query(k, value) for value in v],
                      minimum_should_match=1
                      )
                )
            else:
                must_filter.append(get_term_query(k, v))

    if ranges:
        must_filter.extend([Q('range', **{k: v}) for k, v in ranges.items()])

    s = Search(index=settings.ES_INDEX).query('bool', must=query)
    s = get_sort_query(s, field_order=field_order)

    s = s.post_filter('bool', must=must_filter)

    if aggs:
        apply_aggs_query(s, aggs)

    return s[offset:offset + limit]


def bulk(actions=None, chunk_size=None, **kwargs):
    """Send data in bulk to Elasticsearch."""
    return es_bulk(connections.get_connection(), actions=actions, chunk_size=chunk_size, **kwargs)


FILTER_ID_MAP = {
    'sector': 'sector.id',
    'account_manager': 'account_manager.id',
    'export_to_country': 'export_to_countries.id',
    'future_interest_country': 'future_interest_countries.id',
    'uk_region': 'uk_region.id',
    'trading_address_country': 'trading_address_country.id',
    'address_country': 'address_country.id',
    'adviser': 'adviser.id',
    'client_relationship_manager': 'client_relationship_manager.id',
    'investor_company': 'investor_company.id',
    'investment_type': 'investment_type.id',
    'stage': 'stage.id',
}


def remap_filter_id_field(field):
    """Maps api field to elasticsearch field."""
    return FILTER_ID_MAP.get(field, field)


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
