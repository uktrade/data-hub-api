from unittest import mock

from datahub.search import elasticsearch


def test_get_basic_search_query():
    """Tests basic search query."""
    query = elasticsearch.get_basic_search_query('test', entities=('contact',), offset=5, limit=5)

    assert query.to_dict() == {
        'query': {
            'multi_match': {
                'query': 'test',
                'fields': ['name', '_all']
            }
        },
        'post_filter': {
            'bool': {
                'should': [
                    {'term': {'_type': 'contact'}}
                ]
            }
        },
        'aggs': {
            'count_by_type': {
                'terms': {'field': '_type'}
            }
        },
        'from': 5,
        'size': 5
    }


def test_search_by_entity_query():
    """Tests search by entity."""
    filters = {
        'address_town': 'Woodside',
        'trading_address_country.id': '80756b9a-5d95-e211-a939-e4115bead28a',
    }
    query = elasticsearch.get_search_by_entity_query(
        term='test',
        filters=filters,
        entity='company',
        offset=5,
        limit=5
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [{
                    'term': {
                        '_type': 'company'
                    }}, {
                    'multi_match': {
                        'query': 'test',
                        'fields': ['name', '_all']
                    }}]
            }
        },
        'post_filter': {
            'bool': {
                'must': [{
                    'term': {
                        'address_town': 'Woodside'
                    }}, {
                    'nested': {
                        'path': 'trading_address_country',
                        'query': {
                            'term': {
                                'trading_address_country.id': '80756b9a-5d95-e211-a939-e4115bead28a'
                            }}
                    }}]
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
    """Tests defailed contact search."""
    get_search_by_entity_query.return_value = {}

    elasticsearch.get_search_contact_query(offset=0, limit=5)

    get_search_by_entity_query.assert_called_with(entity='contact', limit=5, offset=0)


def test_remap_fields():
    """Tests fields remapping."""
    filters = {
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

    remapped = elasticsearch.remap_fields(filters)

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
