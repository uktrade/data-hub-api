import pytest
from opensearch_dsl import Mapping

from datahub.company.test.factories import CompanyFactory
from datahub.search.company import CompanySearchApp
from datahub.search.company.models import Company as SearchCompany
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entities_query,
    limit_search_query,
)
from datahub.search.sync_object import sync_object


def test_mapping(opensearch):
    """Test the OpenSearch mapping for a company."""
    mapping = Mapping.from_opensearch(
        CompanySearchApp.search_model.get_write_index(),
    )
    assert mapping.to_dict() == {
        'dynamic': 'false',
        'properties': {
            '_document_type': {
                'type': 'keyword',
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
            'company_number': {
                'normalizer': 'lowercase_asciifolding_normalizer',
                'type': 'keyword',
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
            'export_segment': {'type': 'text'},
            'export_sub_segment': {'type': 'text'},
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
                    'line_1': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'line_2': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'town': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'county': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'postcode': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'area': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
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
                    'country': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
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
                    'line_1': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'line_2': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'town': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'county': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'postcode': {
                        'type': 'text',
                        'fields': {
                            'trigram': {
                                'type': 'text',
                                'analyzer': 'trigram_analyzer',
                            },
                        },
                    },
                    'area': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
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
                    'country': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'keyword'},
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
            'uk_address_postcode': {
                'analyzer': 'postcode_analyzer_v2',
                'search_analyzer': 'postcode_search_analyzer_v2',
                'type': 'text',
            },
            'uk_registered_address_postcode': {
                'analyzer': 'postcode_analyzer_v2',
                'search_analyzer': 'postcode_search_analyzer_v2',
                'type': 'text',
            },
            'one_list_group_global_account_manager': {
                'properties': {
                    'first_name': {
                        'index': False,
                        'type': 'text',
                    },
                    'id': {
                        'type': 'keyword',
                    },
                    'last_name': {
                        'index': False,
                        'type': 'text',
                    },
                    'name': {
                        'index': False,
                        'type': 'text',
                    },
                },
                'type': 'object',
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
            'trading_names': {
                'type': 'text',
                'fields': {
                    'trigram': {
                        'analyzer': 'trigram_analyzer',
                        'type': 'text',
                    },
                },
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
            'latest_interaction_date': {'type': 'date'},
        },
    }


@pytest.mark.django_db
def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query(SearchCompany, 'test', offset=5, limit=5)

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
                                'address.area.name.trigram',
                                'address.country.name.trigram',
                                'address.county.trigram',
                                'address.line_1.trigram',
                                'address.line_2.trigram',
                                'address.postcode',
                                'address.town.trigram',
                                'address.trigram',
                                'address_country.name.trigram',
                                'address_postcode',
                                'companies.name',
                                'companies.name.trigram',
                                'company.name',
                                'company.name.trigram',
                                'company_number',
                                'contact.name',
                                'contact.name.trigram',
                                'contacts.name',
                                'contacts.name.trigram',
                                'country.trigram',
                                'dit_participants.adviser.name',
                                'dit_participants.adviser.name.trigram',
                                'dit_participants.team.name',
                                'dit_participants.team.name.trigram',
                                'email',
                                'event.name',
                                'event.name.trigram',
                                'event_type.name',
                                'event_type.name.trigram',
                                'export_segment',
                                'export_sub_segment',
                                'full_telephone_number',
                                'id',
                                'investor_company.name',
                                'investor_company.name.trigram',
                                'job_title',
                                'job_title.trigram',
                                'name',
                                'name.trigram',
                                'name_with_title',
                                'name_with_title.trigram',
                                'organiser.name.trigram',
                                'project_code',
                                'reference.trigram',
                                'reference_code',
                                'registered_address.area.name.trigram',
                                'registered_address.country.name.trigram',
                                'registered_address.county.trigram',
                                'registered_address.line_1.trigram',
                                'registered_address.line_2.trigram',
                                'registered_address.postcode',
                                'registered_address.town.trigram',
                                'related_programmes.name',
                                'related_programmes.name.trigram',
                                'sector.name',
                                'service.name',
                                'service.name.trigram',
                                'simpleton.name',
                                'subject.english',
                                'subtotal_cost.keyword',
                                'teams.name',
                                'teams.name.trigram',
                                'total_cost.keyword',
                                'trading_names',
                                'trading_names.trigram',
                                'uk_company.name',
                                'uk_company.name.trigram',
                                'uk_region.name',
                                'uk_region.name.trigram',
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
                            '_document_type': 'company',
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
        'from': 5,
        'size': 5,
        'sort': [
            '_score',
            'id',
        ],
        'track_total_hits': True,
    }


@pytest.mark.django_db
def test_limited_get_search_by_entity_query():
    """Tests search by entity."""
    expected_query = {
        'query': {
            'bool': {
                'must': [
                    {
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
                                            'trading_names.trigram',
                                            'reference_code',
                                            'sector.name',
                                            'address.line_1.trigram',
                                            'address.line_2.trigram',
                                            'address.town.trigram',
                                            'address.county.trigram',
                                            'address.area.name.trigram',
                                            'address.postcode',
                                            'address.country.name.trigram',
                                            'registered_address.line_1.trigram',
                                            'registered_address.line_2.trigram',
                                            'registered_address.town.trigram',
                                            'registered_address.county.trigram',
                                            'registered_address.area.name.trigram',
                                            'registered_address.postcode',
                                            'registered_address.country.name.trigram',
                                            'export_segment',
                                            'export_sub_segment',
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
                                    'match': {
                                        'name': {
                                            'query': 'Woodside',
                                            'operator': 'and',
                                        },
                                    },
                                },
                                {
                                    'bool': {
                                        'should': [
                                            {
                                                'match': {
                                                    'address.country.id': {
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
                                        'archived': {
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
        'track_total_hits': True,
        'from': 5,
        'size': 5,
    }

    date = '2017-06-13T09:44:31.062870'
    filter_data = {
        'name': 'Woodside',
        'address.country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'archived_before': date,
        'archived_after': date,
    }
    query = get_search_by_entities_query(
        [SearchCompany],
        term='test',
        filter_data=filter_data,
    )
    query = limit_search_query(
        query,
        offset=5,
        limit=5,
    )

    assert query.to_dict() == expected_query


@pytest.mark.django_db
def test_indexed_doc(opensearch):
    """Test the OpenSearch data of an indexed company."""
    company = CompanyFactory(
        trading_names=['a', 'b'],
    )
    sync_object(CompanySearchApp, company.pk)

    opensearch.indices.refresh()

    indexed_company = opensearch.get(
        index=CompanySearchApp.search_model.get_write_index(),
        id=company.pk,
    )

    assert indexed_company['_id'] == str(company.pk)
    assert indexed_company['_source'].keys() == {
        '_document_type',
        'archived',
        'archived_by',
        'archived_on',
        'archived_reason',
        'business_type',
        'company_number',
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
        'one_list_group_global_account_manager',
        'sector',
        'trading_names',
        'turnover_range',
        'uk_based',
        'uk_region',
        'uk_address_postcode',
        'uk_registered_address_postcode',
        'vat_number',
        'duns_number',
        'website',
        'latest_interaction_date',
        'export_sub_segment',
        'export_segment',
    }
