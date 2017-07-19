import datetime
from unittest import mock

from datahub.search import elasticsearch


def test_get_search_term_query():
    """Tests search term query."""
    query = elasticsearch.get_search_term_query('hello')

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
                    'match': {
                        'name': {
                            'query': 'hello',
                        }
                    }
                }, {
                    'match': {
                        '_all': {
                            'query': 'hello',
                        }
                    }
                }
            ]
        }
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = elasticsearch.get_basic_search_query('test', entities=('contact',), offset=5, limit=5)

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
                        'match': {
                            'name': {
                                'query': 'test',
                            }
                        }
                    }, {
                        'match': {
                            '_all': {
                                'query': 'test',
                            }
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
        'address_town': 'Woodside',
        'trading_address_country.id': '80756b9a-5d95-e211-a939-e4115bead28a',
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
        entity='company',
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
                                            'query': 'test',
                                            'boost': 2
                                        }
                                    }
                                }, {
                                    'match': {
                                        'name': {
                                            'query': 'test',
                                        }
                                    }
                                }, {
                                    'match': {
                                        '_all': {
                                            'query': 'test',
                                        }
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
                        'term': {
                            'address_town': 'Woodside'
                        }
                    }, {
                        'nested': {
                            'path': 'trading_address_country',
                            'query': {
                                'term': {
                                    'trading_address_country.id': '80756b9a-5d95-e211-a939-e4115bead28a'
                                }
                            }
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


@mock.patch('datahub.search.elasticsearch.get_search_by_entity_query')
def test_get_search_company_query(get_search_by_entity_query):
    """Tests detailed company search."""
    get_search_by_entity_query.return_value = {}

    elasticsearch.get_search_company_query(offset=0, limit=5)

    get_search_by_entity_query.assert_called_with(entity='company', limit=5, offset=0)


@mock.patch('datahub.search.elasticsearch.get_search_by_entity_query')
def test_get_search_contact_query(get_search_by_entity_query):
    """Tests detailed contact search."""
    get_search_by_entity_query.return_value = {}

    elasticsearch.get_search_contact_query(offset=0, limit=5)

    get_search_by_entity_query.assert_called_with(entity='contact', limit=5, offset=0)


@mock.patch('datahub.search.elasticsearch.get_search_by_entity_query')
def test_get_search_investment_project_query(get_search_by_entity_query):
    """Tests detailed investment project search."""
    get_search_by_entity_query.return_value = {}

    elasticsearch.get_search_investment_project_query(offset=0, limit=5)

    get_search_by_entity_query.assert_called_with(entity='investment_project', limit=5, offset=0)


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
        'uk_based': False
    }

    remapped = elasticsearch.remap_fields(fields)

    assert 'sector.id' in remapped
    assert 'account_manager.id' in remapped
    assert 'export_to_countries.id' in remapped
    assert 'future_interest_countries.id' in remapped
    assert 'uk_region.id' in remapped
    assert 'trading_address_country.id' in remapped
    assert 'adviser.id' in remapped
    assert 'test' in remapped
    assert 'uk_based' in remapped
    assert remapped['uk_based'] is False


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
