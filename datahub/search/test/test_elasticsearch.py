import datetime
from unittest import mock

import pytest

from .. import elasticsearch


def test_get_search_term_query():
    """Tests search term query."""
    query = elasticsearch.get_search_term_query('hello', fields=('country.id', 'sector'))

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
                    'match': {
                        'name': 'hello'
                    }
                }, {
                    'match_phrase': {
                        'name_trigram': 'hello'
                    }
                }, {
                    'nested': {
                        'path': 'country',
                        'query': {
                            'match': {
                                'country.id': 'hello'
                            }
                        }
                    }
                }, {
                    'match': {
                        'sector': 'hello'
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
    query = elasticsearch.get_basic_search_query(
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
        assert elasticsearch.remap_sort_field(key) == value


def test_date_range_fields():
    """Tests date range fields."""
    now = '2017-06-13T09:44:31.062870'
    fields = {
        'estimated_land_date_after': now,
        'estimated_land_date_before': now,
        'adviser.id': 1234,
    }

    filters, ranges = elasticsearch.date_range_fields(fields)

    assert filters == {
        'adviser.id': 1234
    }
    assert ranges == {
        'estimated_land_date': {
            'gte': datetime.datetime(2017, 6, 13, 9, 44, 31, 62870),
            'lte': datetime.datetime(2017, 6, 13, 9, 44, 31, 62870)
        }
    }


@mock.patch('datahub.search.elasticsearch.es_bulk')
@mock.patch('datahub.search.elasticsearch.connections')
def test_bulk(connections, es_bulk):
    """Tests detailed company search."""
    es_bulk.return_value = {}
    connections.get_connection.return_value = None
    actions = []
    chunk_size = 10
    elasticsearch.bulk(actions=actions, chunk_size=chunk_size)

    es_bulk.assert_called_with(None, actions=actions, chunk_size=chunk_size)


@mock.patch('datahub.search.elasticsearch.settings')
@mock.patch('datahub.search.elasticsearch.connections')
def test_configure_connection(connections, settings):
    """Tests if Heroku connection is configured."""
    settings.HEROKU = True
    settings.ES_URL = 'https://login:password@test:1234'
    connections.configure.return_value = {}

    elasticsearch.configure_connection()

    connections.configure.assert_called_with(default={
        'hosts': [settings.ES_URL],
        'verify_certs': settings.ES_VERIFY_CERTS
    })
