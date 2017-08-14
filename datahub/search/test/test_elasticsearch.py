import datetime
from unittest import mock

from datahub.search import elasticsearch
from datahub.search.models import Company, Contact


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
                        'id': {
                            'query': 'hello'
                        }
                    }
                }, {
                    'match': {
                        'name': {
                            'query': 'hello'
                        }
                    }
                }, {
                    'match_phrase': {
                        'name_trigram': {
                            'query': 'hello'
                        }
                    }
                }, {
                    'nested': {
                        'path': 'country',
                        'query': {
                            'bool': {
                                'must': [
                                    {
                                        'match': {
                                            'country.id': 'hello'
                                        }
                                    }
                                ]
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


def test_get_basic_search_query():
    """Tests basic search query."""
    query = elasticsearch.get_basic_search_query('test', entities=(Contact,), offset=5, limit=5)

    assert query.to_dict() == {
        'query': {
            'bool': {
                'should': [
                    {
                        'match_phrase': {
                            'name_keyword': {
                                'query': 'test',
                                'boost': 2
                            }
                        }
                    }, {
                        'match_phrase': {
                            'id': {
                                'query': 'test'
                            }
                        }
                    }, {
                        'match': {
                            'name': {
                                'query': 'test'
                            }
                        }
                    }, {
                        'match_phrase': {
                            'name_trigram': {
                                'query': 'test'
                            }
                        }
                    }, {
                        'match': {
                            'address_1': 'test'
                        }
                    }, {
                        'match': {
                            'address_2': 'test'
                        }
                    }, {
                        'nested': {
                            'path': 'address_country',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'match': {
                                                'address_country.name': 'test'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }, {
                        'match': {
                            'address_county': 'test'
                        }
                    }, {
                        'match': {
                            'address_town': 'test'
                        }
                    }, {
                        'match': {
                            'email': 'test'
                        }
                    }, {
                        'match': {
                            'notes': 'test'
                        }
                    }
                ]
            }
        },
        'post_filter': {
            'bool': {
                'should': [
                    {
                        'term': {
                            '_type': 'contact'
                        }
                    }
                ]
            }
        },
        'aggs': {
            'count_by_type': {
                'terms': {
                    'field': '_type'
                }
            }
        },
        'from': 5,
        'size': 5
    }


def test_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filters = {
        'address_town': ['Woodside'],
        'trading_address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
    }
    ranges = {
        'estimated_land_date': {
            'gte': date,
            'lte': date
        }
    }
    query = elasticsearch.get_search_by_entity_query(
        term='test',
        filters=filters,
        ranges=ranges,
        entity=Company,
        offset=5,
        limit=5
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            '_type': 'company'
                        }
                    }, {
                        'bool': {
                            'should': [
                                {
                                    'match_phrase': {
                                        'name_keyword': {
                                            'query': 'test', 'boost': 2
                                        }
                                    }
                                }, {
                                    'match_phrase': {
                                        'id': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'match': {
                                        'name': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'match_phrase': {
                                        'name_trigram': {
                                            'query': 'test'
                                        }
                                    }
                                }, {
                                    'nested': {
                                        'path': 'classification',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'classification.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'nested': {
                                        'path': 'export_to_countries',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'export_to_countries.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'nested': {
                                        'path': 'future_interest_countries',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'future_interest_countries.name':
                                                                'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'nested': {
                                        'path': 'registered_address_country',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'registered_address_country.name':
                                                                'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'match': {
                                        'registered_address_town': 'test'
                                    }
                                }, {
                                    'nested': {
                                        'path': 'sector',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'sector.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'nested': {
                                        'path': 'trading_address_country',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'trading_address_country.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'match': {
                                        'trading_address_town': 'test'
                                    }
                                }, {
                                    'nested': {
                                        'path': 'uk_region',
                                        'query': {
                                            'bool': {
                                                'must': [
                                                    {
                                                        'match': {
                                                            'uk_region.name': 'test'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }, {
                                    'match': {
                                        'website': 'test'
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        'post_filter': {
            'bool': {
                'must': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'term': {
                                        'address_town': 'Woodside'
                                    }
                                }
                            ],
                            'minimum_should_match': 1
                        }
                    }, {
                        'bool': {
                            'should': [
                                {
                                    'nested': {
                                        'path': 'trading_address_country',
                                        'query': {
                                            'term': {
                                                'trading_address_country.id':
                                                    '80756b9a-5d95-e211-a939-e4115bead28a'
                                            }
                                        }
                                    }
                                }
                            ],
                            'minimum_should_match': 1
                        }
                    }, {
                        'range': {
                            'estimated_land_date': {
                                'gte': '2017-06-13T09:44:31.062870',
                                'lte': '2017-06-13T09:44:31.062870'
                            }
                        }
                    }
                ]
            }
        },
        'from': 5,
        'size': 5
    }


def test_remap_fields():
    """Tests fields remapping."""
    fields = {
        'sector': 'test',
        'account_manager': 'test',
        'export_to_country': 'test',
        'future_interest_country': 'test',
        'uk_region': 'test',
        'trading_address_country': 'test',
        'adviser': 'test',
        'test': 'test',
        'stage': ['a', 'b'],
        'uk_based': [False]
    }

    remapped = {elasticsearch.remap_filter_id_field(field): value
                for field, value in fields.items()}

    assert 'sector.id' in remapped
    assert 'account_manager.id' in remapped
    assert 'export_to_countries.id' in remapped
    assert 'future_interest_countries.id' in remapped
    assert 'uk_region.id' in remapped
    assert 'trading_address_country.id' in remapped
    assert 'adviser.id' in remapped
    assert 'test' in remapped
    assert 'uk_based' in remapped
    assert remapped['stage.id'] == ['a', 'b']
    assert remapped['uk_based'] == [False]


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
        'hosts': [settings.ES_URL]
    })
