from elasticsearch_dsl import Mapping

from datahub.search.contact import ContactSearchApp
from datahub.search.contact.models import Contact as ESContact
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entity_query,
    limit_search_query,
)


def test_mapping(setup_es):
    """Test the ES mapping for a contact."""
    mapping = Mapping.from_es(
        ContactSearchApp.es_model.get_write_index(),
        ContactSearchApp.name,
    )

    assert mapping.to_dict() == {
        'contact': {
            'properties': {
                'accepts_dit_email_marketing': {'type': 'boolean'},
                'address_1': {'type': 'text'},
                'address_2': {'type': 'text'},
                'address_country': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'address_county': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'address_postcode': {'type': 'text'},
                'address_same_as_company': {'type': 'boolean'},
                'address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'adviser': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'copy_to': ['adviser.name_trigram'],
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'archived': {'type': 'boolean'},
                'archived_by': {
                    'properties': {
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'copy_to': ['archived_by.name_trigram'],
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'archived_on': {'type': 'date'},
                'archived_reason': {'type': 'text'},
                'company': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'copy_to': ['company.name_trigram'],
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                        'trading_name': {
                            'index': False,
                            'type': 'keyword',
                        },
                        'trading_names': {
                            'copy_to': ['company.trading_names_trigram'],
                            'type': 'text',
                        },
                        'trading_names_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'company_sector': {
                    'properties': {
                        'ancestors': {
                            'properties': {'id': {'type': 'keyword'}},
                            'type': 'object',
                        },
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'company_uk_region': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'created_by': {
                    'properties': {
                        'dit_team': {
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                            },
                            'type': 'object',
                        },
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name': {
                            'copy_to': ['created_by.name_trigram'],
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'created_on': {'type': 'date'},
                'email': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'email_alternative': {'type': 'text'},
                'first_name': {
                    'fielddata': True,
                    'type': 'text',
                },
                'id': {'type': 'keyword'},
                'job_title': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'last_name': {
                    'fielddata': True,
                    'type': 'text',
                },
                'modified_on': {'type': 'date'},
                'name': {
                    'type': 'text',
                    'copy_to': ['name_keyword', 'name_trigram'],
                    'fields': {
                        'keyword': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                },
                'name_keyword': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'name_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'notes': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'primary': {'type': 'boolean'},
                'telephone_alternative': {'type': 'text'},
                'telephone_countrycode': {'type': 'keyword'},
                'telephone_number': {'type': 'keyword'},
                'title': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
            },
            'dynamic': 'false',
        },
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query('test', entities=(ESContact,), offset=5, limit=5)

    assert query.to_dict() == {
        'query': {
            'bool': {
                'should': [
                    {
                        'match_phrase': {
                            'name_keyword': {
                                'query': 'test',
                                'boost': 2,
                            },
                        },
                    },
                    {
                        'match_phrase': {
                            'id': 'test',
                        },
                    },
                    {
                        'multi_match': {
                            'query': 'test',
                            'fields': [
                                'address_country.name_trigram',
                                'address_postcode_trigram',
                                'company.name',
                                'company.name_trigram',
                                'company_number',
                                'contact.name',
                                'contact.name_trigram',
                                'dit_adviser.name',
                                'dit_adviser.name_trigram',
                                'dit_team.name',
                                'dit_team.name_trigram',
                                'email',
                                'email_alternative',
                                'event.name',
                                'event.name_trigram',
                                'investor_company.name',
                                'investor_company.name_trigram',
                                'name',
                                'name_trigram',
                                'organiser.name_trigram',
                                'project_code_trigram',
                                'reference_code',
                                'reference_trigram',
                                'registered_address_country.name_trigram',
                                'registered_address_postcode_trigram',
                                'related_programmes.name',
                                'related_programmes.name_trigram',
                                'subject_english',
                                'subtotal_cost_string',
                                'teams.name',
                                'teams.name_trigram',
                                'total_cost_string',
                                'trading_address_country.name_trigram',
                                'trading_address_postcode_trigram',
                                'trading_names',
                                'trading_names_trigram',
                                'uk_company.name',
                                'uk_company.name_trigram',
                                'uk_region.name_trigram',
                            ],
                            'type': 'cross_fields',
                            'operator': 'and',
                        },
                    },
                ],
            },
        },
        'post_filter': {
            'bool': {
                'should': [
                    {
                        'term': {
                            '_type': 'contact',
                        },
                    },
                ],
            },
        },
        'aggs': {
            'count_by_type': {
                'terms': {
                    'field': '_type',
                },
            },
        },
        'from': 5,
        'size': 5,
        'sort': [
            '_score',
            'id',
        ],
    }


def test_get_limited_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filter_data = {
        'address_town': ['Woodside'],
        'trading_address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'estimated_land_date_after': date,
        'estimated_land_date_before': date,
    }
    query = get_search_by_entity_query(
        term='test',
        filter_data=filter_data,
        entity=ESContact,
    )
    query = limit_search_query(
        query,
        offset=5,
        limit=5,
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            '_type': 'contact',
                        },
                    },
                    {
                        'bool': {
                            'should': [
                                {
                                    'match_phrase': {
                                        'name_keyword': {
                                            'query': 'test',
                                            'boost': 2,
                                        },
                                    },
                                },
                                {
                                    'match_phrase': {
                                        'id': 'test',
                                    },
                                },
                                {
                                    'multi_match': {
                                        'query': 'test',
                                        'fields': (
                                            'name',
                                            'name_trigram',
                                            'email',
                                            'email_alternative',
                                            'company.name',
                                            'company.name_trigram',
                                        ),
                                        'type': 'cross_fields',
                                        'operator': 'and',
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        },
        'post_filter': {
            'bool': {
                'must': [
                    {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'address_town': {
                                            'query': 'Woodside',
                                            'operator': 'and',
                                        },
                                    },
                                },
                            ],
                            'minimum_should_match': 1,
                        },
                    },
                    {
                        'bool': {
                            'should': [{
                                'match_phrase': {
                                    'trading_address_country.id':
                                        '80756b9a-5d95-e211-a939-e4115bead28a',
                                },
                            }],
                            'minimum_should_match': 1,
                        },
                    },
                    {
                        'range': {
                            'estimated_land_date': {
                                'gte': '2017-06-13T09:44:31.062870',
                                'lte': '2017-06-13T09:44:31.062870',
                            },
                        },
                    },
                ],
            },
        },
        'from': 5,
        'size': 5,
        'sort': [
            '_score',
            'id',
        ],
    }
