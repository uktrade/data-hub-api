import datetime
from unittest import mock

import pytest

from datahub.search.query_builder import (
    _build_entity_permission_query,
    _build_field_query,
    _build_term_query,
    _split_date_range_fields,
    get_basic_search_query,
)


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
                        'operator': 'and'
                    }
                }
            }
        ),
        (
            'field_name.id',
            'field value',
            {
                'nested': {
                    'path': 'field_name',
                    'query': {
                        'match_phrase': {
                            'field_name.id': 'field value'
                        }
                    }
                }
            }
        ),
        (
            'field_name.name_keyword',
            'field value',
            {
                'nested': {
                    'path': 'field_name',
                    'query': {
                        'match_phrase': {
                            'field_name.name_keyword': 'field value'
                        }
                    }
                }
            }
        ),
        (
            'field_name.prop',
            'field value',
            {
                'nested': {
                    'path': 'field_name',
                    'query': {
                        'match': {
                            'field_name.prop': {
                                'query': 'field value',
                                'operator': 'and'
                            }
                        }
                    }
                }
            }
        ),
        (
            'field_name_exists',
            True,
            {
                'bool': {
                    'must': [
                        {
                            'exists': {
                                'field': 'field_name'
                            }
                        }
                    ]
                }
            }
        ),
        (
            'field_name_exists',
            False,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name'
                            }
                        }
                    ]
                }
            }
        ),
        (
            'field_name',
            None,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name'
                            }
                        }
                    ]
                }
            }
        ),
        (
            'field_name_exists',
            None,
            {
                'bool': {
                    'must_not': [
                        {
                            'exists': {
                                'field': 'field_name'
                            }
                        }
                    ]
                }
            }
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
                                    'operator': 'and'
                                }
                            }
                        },
                        {
                            'match': {
                                'field_name': {
                                    'query': 'field value 2',
                                    'operator': 'and'
                                }
                            }
                        }
                    ]
                }
            }
        ),
    )
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
                            'match_phrase': {
                                'name_keyword': {
                                    'query': 'hello',
                                    'boost': 2
                                }
                            }
                        }, {
                            'match_phrase': {
                                'id': 'hello'
                            }
                        }, {
                            'multi_match': {
                                'query': 'hello',
                                'fields': ('country.id', 'sector'),
                                'type': 'cross_fields',
                                'operator': 'and'
                            }
                        }
                    ]
                }
            }
        ),
        (
            '',
            {
                'match_all': {}
            }
        )
    )
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
    )
)
def test_offset_near_max_results(offset, limit, expected_size):
    """Tests limit clipping when near max_results."""
    query = get_basic_search_query(
        'test', entities=(mock.Mock(),), offset=offset, limit=limit
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

    filters, ranges = _split_date_range_fields(fields)

    assert filters == {
        'adviser.id': 1234
    }
    assert ranges == {
        'estimated_land_date': {
            'gte': now,
            'lte': now
        }
    }


@pytest.mark.parametrize(
    'filters,expected',
    (
        # An empty dict of conditions should mean that there are no conditions that would permit
        # access.
        (
            {},
            {
                'match_none': {}
            }
        ),
        (
            None,
            None
        ),
        (
            {
                'field_name': 'field value'
            },
            {
                'bool': {
                    'should': [
                        {'term': {'field_name': 'field value'}}
                    ]
                }
            }
        ),
        (
            {
                'field_name1': 'field value 1',
                'field_name2': 'field value 2'
            },
            {
                'bool': {
                    'should': [
                        {'term': {'field_name1': 'field value 1'}},
                        {'term': {'field_name2': 'field value 2'}}
                    ]
                }
            }
        )
    )
)
def test_build_entity_permission_query_no_conditions(filters, expected):
    """Test for the _build_entity_permission_query function."""
    query = _build_entity_permission_query(permission_filters=filters)
    if expected is None:
        assert query is None
    else:
        assert query.to_dict() == expected
