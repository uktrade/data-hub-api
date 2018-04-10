import datetime
from unittest import mock

import pytest

from datahub.search.query_builder import (
    _get_entity_permission_query,
    _get_search_term_query,
    _remap_sort_field,
    _split_date_range_fields,
    get_basic_search_query,
)


def test_get_search_term_query():
    """Tests search term query."""
    query = _get_search_term_query('hello', fields=('country.id', 'sector'))

    assert query.to_dict() == {
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


def test_remap_sort_field():
    """Test sort fields remapping."""
    fields = {
        'name': 'name_keyword'
    }

    for key, value in fields.items():
        assert _remap_sort_field(key) == value


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


def test_get_entity_permission_query_no_conditions():
    """
    Test that _get_entity_permission_query() correctly handles an empty dict
    of conditions.

    (An empty dict of conditions should mean that there are no conditions that would permit
    access.)
    """
    query = _get_entity_permission_query(permission_filters={})
    assert query.to_dict() == {
        'match_none': {}
    }
