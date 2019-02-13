import pytest
from elasticsearch_dsl import Mapping

from datahub.company.test.factories import CompanyFactory
from datahub.search import elasticsearch
from datahub.search.company import CompanySearchApp
from datahub.search.company.models import Company as ESCompany
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entity_query,
    limit_search_query,
)


def test_mapping(setup_es):
    """Test the ES mapping for a company."""
    mapping = Mapping.from_es(
        CompanySearchApp.es_model.get_write_index(),
        CompanySearchApp.name,
    )

    assert mapping.to_dict() == {
        'company': {
            'dynamic': 'false',
            'properties': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['archived_by.name_trigram'],
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
                'business_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'companies_house_data': {
                    'properties': {
                        'company_number': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {'type': 'keyword'},
                    },
                    'type': 'object',
                },
                'company_number': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'contacts': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['contacts.name_trigram'],
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
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'duns_number': {'type': 'keyword'},
                'employee_range': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'export_experience_category': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'export_to_countries': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'future_interest_countries': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'global_headquarters': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'headquarter_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'id': {'type': 'keyword'},
                'modified_on': {'type': 'date'},
                'name': {
                    'type': 'text',
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
                'reference_code': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'address': {
                    'type': 'object',
                    'properties': {
                        'line_1': {'index': False, 'type': 'text'},
                        'line_2': {'index': False, 'type': 'text'},
                        'town': {'index': False, 'type': 'text'},
                        'county': {'index': False, 'type': 'text'},
                        'postcode': {
                            'type': 'text',
                            'fields': {
                                'trigram': {
                                    'type': 'text',
                                    'analyzer': 'trigram_analyzer',
                                },
                            },
                        },
                        'country': {
                            'type': 'object',
                            'properties': {
                                'id': {'index': False, 'type': 'keyword'},
                                'name': {
                                    'type': 'text',
                                    'fields': {
                                        'trigram': {
                                            'type': 'text',
                                            'analyzer': 'trigram_analyzer',
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                'registered_address': {
                    'type': 'object',
                    'properties': {
                        'line_1': {'index': False, 'type': 'text'},
                        'line_2': {'index': False, 'type': 'text'},
                        'town': {'index': False, 'type': 'text'},
                        'county': {'index': False, 'type': 'text'},
                        'postcode': {
                            'type': 'text',
                            'fields': {
                                'trigram': {
                                    'type': 'text',
                                    'analyzer': 'trigram_analyzer',
                                },
                            },
                        },
                        'country': {
                            'type': 'object',
                            'properties': {
                                'id': {'index': False, 'type': 'keyword'},
                                'name': {
                                    'type': 'text',
                                    'fields': {
                                        'trigram': {
                                            'type': 'text',
                                            'analyzer': 'trigram_analyzer',
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                'registered_address_1': {'type': 'text'},
                'registered_address_2': {'type': 'text'},
                'registered_address_country': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['registered_address_country.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'registered_address_county': {'type': 'text'},
                'registered_address_postcode': {
                    'copy_to': ['registered_address_postcode_trigram'],
                    'type': 'text',
                },
                'registered_address_postcode_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'registered_address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'sector': {
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
                'suggest': {
                    'analyzer': 'simple',
                    'max_input_length': 50,
                    'preserve_position_increments': True,
                    'preserve_separators': True,
                    'type': 'completion',
                },
                'trading_address_1': {'type': 'text'},
                'trading_address_2': {'type': 'text'},
                'trading_address_country': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['trading_address_country.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'trading_address_county': {'type': 'text'},
                'trading_address_postcode': {
                    'copy_to': ['trading_address_postcode_trigram'],
                    'type': 'text',
                },
                'trading_address_postcode_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'trading_address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'trading_names': {
                    'copy_to': ['trading_names_trigram'],
                    'type': 'text',
                },
                'trading_names_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'turnover_range': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'uk_based': {'type': 'boolean'},
                'uk_region': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'vat_number': {
                    'index': False,
                    'type': 'keyword',
                },
                'website': {'type': 'text'},
            },
        },
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query('test', entities=(ESCompany,), offset=5, limit=5)

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
                            'fields': [
                                'address_country.name_trigram',
                                'address_postcode_trigram',
                                'company.name',
                                'company.name_trigram',
                                'company_number',
                                'contact.name',
                                'contact.name_trigram',
                                'contacts.name',
                                'contacts.name.trigram',
                                'dit_adviser.name',
                                'dit_adviser.name_trigram',
                                'dit_team.name',
                                'dit_team.name_trigram',
                                'email',
                                'email_alternative',
                                'event.name',
                                'event.name_trigram',
                                'id',
                                'investor_company.name',
                                'investor_company.name_trigram',
                                'name',
                                'name.trigram',
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
                            '_type': 'company',
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


def test_limited_get_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filter_data = {
        'address_town': ['Woodside'],
        'trading_address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'estimated_land_date_before': date,
        'estimated_land_date_after': date,
    }
    query = get_search_by_entity_query(
        ESCompany,
        term='test',
        filter_data=filter_data,
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
                            '_type': 'company',
                        },
                    }, {
                        'bool': {
                            'should': [
                                {
                                    'match': {
                                        'name.keyword': {
                                            'query': 'test',
                                            'boost': 2,
                                        },
                                    },
                                }, {
                                    'multi_match': {
                                        'query': 'test',
                                        'fields': (
                                            'id',
                                            'name',
                                            'name.trigram',
                                            'company_number',
                                            'trading_names',
                                            'trading_names_trigram',
                                            'reference_code',
                                            'registered_address_country.name_trigram',
                                            'registered_address_postcode_trigram',
                                            'trading_address_country.name_trigram',
                                            'trading_address_postcode_trigram',
                                        ),
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
                                }, {
                                    'bool': {
                                        'should': [
                                            {
                                                'match': {
                                                    'trading_address_country.id': {
                                                        'query':
                                                            '80756b9a-5d95-e211-a939-e4115bead28a',
                                                        'operator': 'and',
                                                    },
                                                },
                                            },
                                        ],
                                        'minimum_should_match': 1,
                                    },
                                }, {
                                    'range': {
                                        'estimated_land_date': {
                                            'lte': '2017-06-13T09:44:31.062870',
                                            'gte': '2017-06-13T09:44:31.062870',
                                        },
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        },
        'sort': [
            '_score',
            'id',
        ],
        'from': 5,
        'size': 5,
    }


@pytest.mark.django_db
def test_indexed_doc(setup_es):
    """Test the ES data of an indexed company."""
    company = CompanyFactory(
        trading_names=['a', 'b'],
    )

    doc = ESCompany.es_document(company)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    setup_es.indices.refresh()

    indexed_company = setup_es.get(
        index=CompanySearchApp.es_model.get_write_index(),
        doc_type=CompanySearchApp.name,
        id=company.pk,
    )

    assert indexed_company['_id'] == str(company.pk)
    assert indexed_company['_source'].keys() == {
        'archived',
        'archived_by',
        'archived_on',
        'archived_reason',
        'business_type',
        'companies_house_data',
        'company_number',
        'contacts',
        'created_on',
        'description',
        'employee_range',
        'export_experience_category',
        'export_to_countries',
        'future_interest_countries',
        'headquarter_type',
        'id',
        'modified_on',
        'name',
        'global_headquarters',
        'reference_code',
        'address',
        'registered_address',
        'registered_address_1',
        'registered_address_2',
        'registered_address_country',
        'registered_address_county',
        'registered_address_postcode',
        'registered_address_town',
        'sector',
        'suggest',
        'trading_address_1',
        'trading_address_2',
        'trading_address_country',
        'trading_address_county',
        'trading_address_postcode',
        'trading_address_town',
        'trading_names',
        'turnover_range',
        'uk_based',
        'uk_region',
        'vat_number',
        'duns_number',
        'website',
    }
