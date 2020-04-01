import datetime
from unittest import mock
from uuid import UUID

import pytest

from datahub.core.constants import Country as CountryConstant
from datahub.search.query_builder import (
    _build_entity_permission_query,
    _build_field_query,
    _build_term_query,
    _split_range_fields,
    build_autocomplete_query,
    get_basic_search_query,
    get_search_by_entities_query,
)
from datahub.search.test.search_support.relatedmodel.apps import RelatedModelSearchApp
from datahub.search.test.search_support.simplemodel.apps import SimpleModelSearchApp
from datahub.search.utils import SearchOrdering, SortDirection


@pytest.mark.parametrize(
    'field,value,expected',
    (
        (
            'field_name',
            'field value',
            {
                'match': {
                    'field_name': {
                        'query': 'field value',
                        'operator': 'and',
                    },
                },
            },
        ),
        (
            'field_name.id',
            'field value',
            {
                'match': {
                    'field_name.id': {
                        'query': 'field value',
                        'operator': 'and',
                    },
                },
            },
        ),
        (
            'field_name.name.keyword',
            'field value',
            {
                'match': {
                    'field_name.name.keyword': {
                        'query': 'field value',
                        'operator': 'and',
                    },
                },
            },
        ),
        (
            'field_name.prop',
            'field value',
            {
                'match': {
                    'field_name.prop': {
                        'query': 'field value',
                        'operator': 'and',
                    },
                },
            },
        ),
        (
            'field_name_exists',
            True,
            {
                'bool': {
                    'must': [
                        {
                            'exists': {
                                'field': 'field_name',
                            },
                        },
                    ],
                },
            },
        ),
        (
            'field_name_exists',
            False,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name',
                            },
                        },
                    ],
                },
            },
        ),
        (
            'field_name',
            None,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name',
                            },
                        },
                    ],
                },
            },
        ),
        (
            'field_name_exists',
            None,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name',
                            },
                        },
                    ],
                },
            },
        ),
        (
            'field_name',
            ['field value 1', 'field value 2'],
            {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        {
                            'match': {
                                'field_name': {
                                    'query': 'field value 1',
                                    'operator': 'and',
                                },
                            },
                        },
                        {
                            'match': {
                                'field_name': {
                                    'query': 'field value 2',
                                    'operator': 'and',
                                },
                            },
                        },
                    ],
                },
            },
        ),
    ),
)
def test_build_field_query(field, value, expected):
    """Test for the _build_field_query function."""
    assert _build_field_query(field, value).to_dict() == expected


@pytest.mark.parametrize(
    'term,expected',
    (
        (
            'hello',
            {
                'bool': {
                    'should': [
                        {
                            'match': {
                                'name.keyword': {
                                    'query': 'hello',
                                    'boost': 2,
                                },
                            },
                        },
                        {
                            'multi_match': {
                                'query': 'hello',
                                'fields': ('country.id', 'sector'),
                                'type': 'cross_fields',
                                'operator': 'and',
                            },
                        },
                    ],
                },
            },
        ),
        (
            '',
            {
                'match_all': {},
            },
        ),
    ),
)
def test_build_term_query(term, expected):
    """Tests search term query."""
    query = _build_term_query(term, fields=('country.id', 'sector'))
    assert query.to_dict() == expected


@pytest.mark.parametrize(
    'offset,limit,expected_size', (
        (8950, 1000, 1000),
        (9950, 1000, 50),
        (10000, 1000, 0),
    ),
)
def test_offset_near_max_results(offset, limit, expected_size):
    """Tests limit clipping when near max_results."""
    query = get_basic_search_query(
        mock.Mock(), 'test', offset=offset, limit=limit,
    )

    query_dict = query.to_dict()
    assert query_dict['from'] == offset
    assert query_dict['size'] == expected_size


def test_date_range_fields():
    """Tests date range fields."""
    now = datetime.datetime(2017, 6, 13, 9, 44, 31, 62870)
    fields = {
        'estimated_land_date_after': now,
        'estimated_land_date_before': now,
        'adviser.id': 1234,
    }

    filters, ranges = _split_range_fields(fields)

    assert filters == {
        'adviser.id': 1234,
    }
    assert ranges == {
        'estimated_land_date': {
            'gte': now,
            'lte': now,
        },
    }


@pytest.mark.parametrize(
    'filters,expected',
    (
        # An empty list of conditions should mean that there are no conditions
        # that would permit access.
        (
            [],
            {
                'match_none': {},
            },
        ),
        (
            None,
            None,
        ),
        (
            [
                ('field_name', 'field value'),
            ],
            {
                'bool': {
                    'should': [
                        {'term': {'field_name': 'field value'}},
                    ],
                },
            },
        ),
        (
            [
                ('field_name1', 'field value 1'),
                ('field_name2', 'field value 2'),
            ],
            {
                'bool': {
                    'should': [
                        {'term': {'field_name1': 'field value 1'}},
                        {'term': {'field_name2': 'field value 2'}},
                    ],
                },
            },
        ),
    ),
)
def test_build_entity_permission_query_no_conditions(filters, expected):
    """Test for the _build_entity_permission_query function."""
    query = _build_entity_permission_query(permission_filters=filters)
    if expected is None:
        assert query is None
    else:
        assert query.to_dict() == expected


@pytest.mark.parametrize(
    'keyword,size,only_fields,context,expected',
    (
        (
            'hello',
            20,
            None,
            {},
            {
                'suggest': {
                    'autocomplete': {
                        'completion': {'field': 'suggest', 'size': 20},
                        'text': 'hello',
                    },
                },
            },
        ),
        (
            'goodbye',
            1,
            ['id', 'name'],
            {},
            {
                '_source': {'includes': ['id', 'name']},
                'suggest': {
                    'autocomplete': {
                        'completion': {'field': 'suggest', 'size': 1},
                        'text': 'goodbye',
                    },
                },
            },
        ),
        (
            'goodbye',
            1,
            ['id', 'name'],
            {'country': [CountryConstant.canada.value.id]},
            {
                '_source': {'includes': ['id', 'name']},
                'suggest': {
                    'autocomplete': {
                        'completion': {
                            'field': 'suggest',
                            'size': 1,
                            'contexts': {'country': [CountryConstant.canada.value.id]},
                        },
                        'text': 'goodbye',
                    },
                },
            },
        ),
        (
            'goodbye',
            1,
            ['id', 'name'],
            {'country': 'hello'},
            {
                '_source': {'includes': ['id', 'name']},
                'suggest': {
                    'autocomplete': {
                        'completion': {
                            'field': 'suggest',
                            'size': 1,
                            'contexts': {'country': 'hello'},
                        },
                        'text': 'goodbye',
                    },
                },
            },
        ),
    ),
)
def test_build_autocomplete_search_query(keyword, size, only_fields, context, expected):
    """Test for building an autocomplete search query."""
    query = build_autocomplete_query(
        SimpleModelSearchApp.es_model,
        keyword,
        size,
        only_fields,
        context,
    )
    assert query.to_dict() == expected
    assert query._index == [SimpleModelSearchApp.es_model.get_read_alias()]


@pytest.mark.parametrize(
    (
        'term',
        'filter_data',
        'composite_field_mapping',
        'permission_filters',
        'ordering',
        'fields_to_include',
        'fields_to_exclude',
        'expected_query',
    ),
    (
        # minimal
        (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'bool': {
                                    'should': [
                                        {
                                            'match': {
                                                'name.keyword': {
                                                    'query': None,
                                                    'boost': 2,
                                                },
                                            },
                                        },
                                        {
                                            'multi_match': {
                                                'query': None,
                                                'fields': ('name', 'name.trigram'),
                                                'type': 'cross_fields',
                                                'operator': 'and',
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                        'filter': [{'bool': {}}],
                    },
                },
                'sort': ['_score', 'id'],
            },
        ),

        # complete
        (
            'search term',
            {
                'name': ['test'],
            },
            {
                'name': [
                    'name.trigram',
                ],
            },
            [
                (
                    'created_by.dit_team.id',
                    UUID('00000000-0000-0000-0000-000000000000'),
                ),
            ],
            SearchOrdering('id', SortDirection.desc),
            ['id'],
            ['name'],
            {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'bool': {
                                    'should': [
                                        {
                                            'match': {
                                                'name.keyword': {
                                                    'query': 'search term',
                                                    'boost': 2,
                                                },
                                            },
                                        },
                                        {
                                            'multi_match': {
                                                'query': 'search term',
                                                'fields': ('name', 'name.trigram'),
                                                'type': 'cross_fields',
                                                'operator': 'and',
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                        'filter': [
                            {
                                'bool': {
                                    'should': [
                                        {
                                            'term': {
                                                'created_by.dit_team.id': UUID(
                                                    '00000000-0000-0000-0000-000000000000',
                                                ),
                                            },
                                        },
                                    ],
                                },
                            },
                            {
                                'bool': {
                                    'must': [
                                        {
                                            'bool': {
                                                'should': [
                                                    {
                                                        'bool': {
                                                            'should': [
                                                                {
                                                                    'match': {
                                                                        'name.trigram': {
                                                                            'query': 'test',
                                                                            'operator': 'and',
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                            'minimum_should_match': 1,
                                                        },
                                                    },
                                                ],
                                                'minimum_should_match': 1,
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
                'sort': [
                    {
                        'id': {
                            'order': SortDirection.desc,
                            'missing': '_last',
                        },
                    },
                    'id',
                ],
                '_source': {
                    'includes': ['id'],
                    'excludes': ['name'],
                },
            },
        ),
    ),
)
def test_get_search_by_entities_query(
    term,
    filter_data,
    composite_field_mapping,
    permission_filters,
    ordering,
    fields_to_include,
    fields_to_exclude,
    expected_query,
):
    """Tests for the get_search_by_entities_query function."""
    query = get_search_by_entities_query(
        [SimpleModelSearchApp.es_model],
        term=term,
        filter_data=filter_data,
        composite_field_mapping=composite_field_mapping,
        permission_filters=permission_filters,
        ordering=ordering,
        fields_to_include=fields_to_include,
        fields_to_exclude=fields_to_exclude,
    )
    assert query.to_dict() == expected_query
    assert query._index == [SimpleModelSearchApp.es_model.get_read_alias()]


def test_get_search_by_multiple_entities_query():
    """Tests for the get_search_by_entities_query function."""
    query = get_search_by_entities_query(
        [
            SimpleModelSearchApp.es_model,
            RelatedModelSearchApp.es_model,
        ],
        term=None,
        filter_data=None,
        composite_field_mapping=None,
        permission_filters=None,
        ordering=None,
        fields_to_include=None,
        fields_to_exclude=None,
    )
    expected_query = {
        'query': {
            'bool': {
                'filter': [
                    {
                        'bool': {},
                    },
                ],
                'must': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'name.keyword': {
                                            'boost': 2,
                                            'query': None,
                                        },
                                    },
                                },
                                {
                                    'multi_match': {
                                        'fields': (
                                            'name',
                                            'name.trigram',
                                        ),
                                        'operator': 'and',
                                        'query': None,
                                        'type': 'cross_fields',
                                    },
                                },
                            ],
                        },
                    },
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'name.keyword': {
                                            'boost': 2,
                                            'query': None,
                                        },
                                    },
                                },
                                {
                                    'multi_match': {
                                        'fields': ('simpleton.name',),
                                        'operator': 'and',
                                        'query': None,
                                        'type': 'cross_fields',
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        },
        'sort': [
            '_score', 'id',
        ],
    }
    assert query.to_dict() == expected_query
    assert query._index == [
        SimpleModelSearchApp.es_model.get_read_alias(),
        RelatedModelSearchApp.es_model.get_read_alias(),
    ]


@mock.patch('datahub.search.query_builder.get_global_search_apps_as_mapping')
def test_get_basic_search_query(mocked_get_global_search_apps_as_mapping):
    """Test for get_basic_search_query."""
    search_app = SimpleModelSearchApp
    mocked_get_global_search_apps_as_mapping.return_value = {
        search_app.name: search_app,
    }

    query = get_basic_search_query(
        search_app.es_model,
        'test',
        permission_filters_by_entity={
            search_app.name: [('name', 'perm')],
        },
        offset=2,
        limit=3,
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'should': [
                    {
                        'match': {
                            'name.keyword': {
                                'query': 'test',
                                'boost': 2,
                            },
                        },
                    },
                    {
                        'multi_match': {
                            'query': 'test',
                            'fields': ['name', 'name.trigram'],
                            'type': 'cross_fields',
                            'operator': 'and',
                        },
                    },
                ],
                'filter': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'bool': {
                                        'should': [
                                            {
                                                'term': {
                                                    'name': 'perm',
                                                },
                                            },
                                        ],
                                        'must': [
                                            {
                                                'term': {
                                                    '_document_type': search_app.name,
                                                },
                                            },
                                        ],
                                        'minimum_should_match': 1,
                                    },
                                },
                            ],
                        },
                    },
                ],
                'minimum_should_match': 1,
            },
        },
        'post_filter': {
            'bool': {
                'should': [
                    {
                        'term': {
                            '_document_type': search_app.name,
                        },
                    },
                ],
            },
        },
        'aggs': {
            'count_by_type': {
                'terms': {
                    'field': '_document_type',
                },
            },
        },
        'sort': [
            '_score',
            'id',
        ],
        'from': 2,
        'size': 3,
    }
