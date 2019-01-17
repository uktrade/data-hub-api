from collections import defaultdict
from itertools import chain

from elasticsearch_dsl import Search
from elasticsearch_dsl.query import (
    Bool,
    Exists,
    Match,
    MatchAll,
    MultiMatch,
    Query,
    Range,
    Term,
)

from datahub.search.apps import EXCLUDE_ALL, get_global_search_apps_as_mapping

MAX_RESULTS = 10000
FIELD_REMAPPING = {
    'name': 'name.keyword',
}


class MatchNone(Query):
    """match_none query. This isn't defined in the Elasticsearch DSL library."""

    name = 'match_none'


def get_basic_search_query(
        term,
        entities=None,
        permission_filters_by_entity=None,
        ordering=None,
        offset=0,
        limit=100,
):
    """Performs basic search looking for name and then SEARCH_FIELDS in entity.

    Also returns number of results in other entities.

    :param permission_filters_by_entity: List of pairs of entities and corresponding permission
                                         filters. Only entities in this list are included in the
                                         results, and those are entities are also filtered using
                                         the corresponding permission filters.
    """
    limit = _clip_limit(offset, limit)

    search_apps = tuple(get_global_search_apps_as_mapping().values())
    indices = [app.es_model.get_read_alias() for app in search_apps]
    fields = set(chain.from_iterable(app.es_model.SEARCH_FIELDS for app in search_apps))

    # Sort the fields so that this function is deterministic
    # and the same query is always generated with the same inputs
    fields = sorted(fields)

    query = _build_term_query(term, fields=fields)
    search = Search(index=indices).query(query)

    permission_query = _build_global_permission_query(permission_filters_by_entity)
    if permission_query:
        search = search.filter(permission_query)

    entity_type_subqueries = [Term(_type=entity._doc_type.name) for entity in entities]

    search = search.post_filter(
        Bool(should=entity_type_subqueries),
    )
    search = _apply_sorting_to_query(search, ordering)
    search.aggs.bucket(
        'count_by_type', 'terms', field='_type',
    )

    return search[offset:offset + limit]


def get_search_by_entity_query(
        term=None,
        filter_data=None,
        composite_field_mapping=None,
        permission_filters=None,
        entity=None,
        ordering=None,
):
    """
    Performs filtered search for given terms in given entity.

    :param permission_filters: dict of field names and values. These represent rules that records
                               must match one of to be included in the results.
    """
    query = [Term(_type=entity._doc_type.name)]
    if term != '':
        query.append(_build_term_query(term, fields=entity.SEARCH_FIELDS))

    filters, ranges = _split_date_range_fields(filter_data)

    # document must match all filters in the list (and)
    must_filter = _build_must_queries(filters, ranges, composite_field_mapping)

    s = Search(
        index=entity.get_read_alias(),
    ).query(
        Bool(must=query),
    )

    permission_query = _build_entity_permission_query(permission_filters)
    if permission_query:
        s = s.filter(permission_query)

    s = s.post_filter(
        Bool(must=must_filter),
    )
    return _apply_sorting_to_query(s, ordering)


def build_autocomplete_query(es_model, keyword_search, limit, only_return_fields):
    """Builds the query for autocomplete search and applies source filtering."""
    index = es_model.get_read_alias()
    autocomplete_search = es_model.search(index=index)
    if only_return_fields:
        autocomplete_search = autocomplete_search.extra(_source={'include': only_return_fields})
    return autocomplete_search.suggest(
        'autocomplete',
        keyword_search,
        completion={'field': 'suggest', 'size': limit},
    )


def limit_search_query(query, offset=0, limit=100):
    """Limits search query to the page defined by offset and limit."""
    limit = _clip_limit(offset, limit)
    return query[offset:offset + limit]


def _split_date_range_fields(fields):
    """Finds and formats range fields."""
    filters = {}
    ranges = defaultdict(dict)

    for k, v in fields.items():
        if k.endswith('_before') or k.endswith('_after'):
            range_key = k[:k.rindex('_')]

            if k.endswith('_before'):
                ranges[range_key]['lte'] = fields[k]
            if k.endswith('_after'):
                ranges[range_key]['gte'] = fields[k]

            continue

        filters.update({k: v})

    return filters, ranges


def _clip_limit(offset, limit):
    return max(min(limit, MAX_RESULTS - offset), 0)


def _build_global_permission_query(permission_filters_by_entity):
    """
    Returns the filter query to use to enforce permissions in global search.

    See also:
        get_basic_search_query()

    """
    # None means that permissions aren't in effect for the current query. None is returned to
    # indicate that a filter query should not be applied.
    if permission_filters_by_entity is None:
        return None

    subqueries = list(_build_global_permission_subqueries(permission_filters_by_entity))
    # Check if there are any should subqueries (of which at least one should be matched).
    # If there are no conditions, return MatchNone() to ensure that all results are filtered out
    #  (as you can't meet at least one condition when there are no conditions).
    if len(subqueries) > 0:
        return Bool(
            should=subqueries,
        )
    return MatchNone()


def _build_global_permission_subqueries(permission_filters_by_entity):
    for entity, filter_args in permission_filters_by_entity.items():
        query = Term(_type=entity)
        entity_condition = _build_entity_permission_query(filter_args)

        if entity_condition is not None:
            query &= entity_condition

        yield query


def _build_entity_permission_query(permission_filters):
    """Builds the filter query to apply to enforce permissions for a model."""
    # None is used when there is no filtering to apply for the entity,
    # Returns None to indicate that no filter query should be used.
    if permission_filters is None:
        return None

    if permission_filters is EXCLUDE_ALL:
        return MatchNone()

    subqueries = [Term(**{field: value}) for field, value in permission_filters]

    # Check if there are any should subqueries (of which at least one should be matched).
    # If there are no conditions, return MatchNone() to ensure that all results are filtered out
    #  (as you can't meet at least one condition when there are no conditions).
    if len(subqueries) > 0:
        return Bool(
            should=subqueries,
        )
    return MatchNone()


def _build_term_query(term, fields=None):
    """Builds a term query."""
    if term == '':
        return MatchAll()

    should_query = [
        # Promote exact name match
        Match(**{'name.keyword': {'query': term, 'boost': 2}}),
        # Cross match fields
        MultiMatch(
            query=term,
            fields=fields,
            type='cross_fields',
            operator='and',
        ),
    ]

    return Bool(should=should_query)


def _build_exists_query(field, value):
    """Builds an exists query."""
    real_field = field[:field.rindex('_')]

    kind = 'must' if value else 'must_not'
    query = {
        kind: Exists(field=real_field),
    }
    return Bool(**query)


def _build_single_field_query(field, value):
    """
    Used by _build_field_query and always expecting value as a single value.
    You should never need to use this, it's more likely you want _build_field_query instead.
    """
    if field.endswith('_exists'):
        return _build_exists_query(field, value)

    # Implicit exists query
    if value is None:
        parent_field = field.rsplit('.', maxsplit=1)[0]
        return _build_exists_query(f'{parent_field}_exists', False)

    field_query = {
        'query': value,
        'operator': 'and',
    }
    return Match(**{field: field_query})


def _build_field_query(field, value):
    """Builds a field query."""
    if isinstance(value, list):
        # perform "or" query
        should_filter = [
            _build_single_field_query(field, single_value) for single_value in value
        ]
        return Bool(should=should_filter, minimum_should_match=1)

    return _build_single_field_query(field, value)


def _build_field_queries(filters):
    """
    Builds field queries.
    Same as _build_field_query but expects a dict of field/values and returns a list of queries.
    """
    return [
        _build_field_query(field, value)
        for field, value in filters.items()
    ]


def _build_range_queries(filters):
    """Builds range queries."""
    return [
        Range(**{field: value})
        for field, value in filters.items()
    ]


def _build_nested_queries(field, nested_filters):
    """Builds nested queries."""
    normalised_nested_filters = {
        f'{field}_{nested_field}': nested_value
        for nested_field, nested_value in nested_filters.items()
    }

    filters, ranges = _split_date_range_fields(normalised_nested_filters)
    return [
        *_build_field_queries(filters),
        *_build_range_queries(ranges),
    ]


def _build_must_queries(filters, ranges, composite_field_mapping):
    """Builds a "must" filter query."""
    must_filter = []

    for field, value in filters.items():
        should_filters = None

        # get nested "or" filters
        if composite_field_mapping and field in composite_field_mapping:
            # process composite filters
            composite_fields = composite_field_mapping[field]
            should_filters = _build_field_queries(
                {composite_field: value for composite_field in composite_fields},
            )
        elif isinstance(value, dict):
            should_filters = _build_nested_queries(field, value)

        if should_filters:
            # builds an "or" query for given list of fields
            must_filter.append(
                Bool(should=should_filters, minimum_should_match=1),
            )
        else:
            must_filter.append(
                _build_field_query(field, value),
            )

    if ranges:
        must_filter.extend(_build_range_queries(ranges))

    return must_filter


def _apply_sorting_to_query(query, ordering):
    """Applies sorting to the query."""
    if ordering is None:
        return query.sort('_score', 'id')

    tokens = ordering.rsplit(':', maxsplit=1)
    order = tokens[1] if len(tokens) > 1 else 'asc'
    field_name = tokens[0]

    sort_params = {
        'order': order,
        'missing': '_first' if order == 'asc' else '_last',
    }

    # remap field name if necessary
    field_name = FIELD_REMAPPING.get(field_name, field_name)

    return query.sort(
        {field_name: sort_params},
        'id',
    )
