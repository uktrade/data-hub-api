import pytest
from elasticsearch_dsl import Mapping

from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.search import elasticsearch
from datahub.search.companieshousecompany import CompaniesHouseCompanySearchApp
from datahub.search.companieshousecompany.models import (
    CompaniesHouseCompany as ESCompaniesHouseCompany,
)
from datahub.search.query_builder import get_search_by_entity_query


def test_mapping(setup_es):
    """Test the ES mapping for a companies house company."""
    mapping = Mapping.from_es(
        CompaniesHouseCompanySearchApp.es_model.get_target_index_name(),
        CompaniesHouseCompanySearchApp.name,
    )

    assert mapping.to_dict() == {
        'companieshousecompany': {
            'dynamic': 'false',
            'properties': {
                'company_category': {
                    'index': False,
                    'type': 'keyword',
                },
                'company_number': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'company_status': {
                    'index': False,
                    'type': 'keyword',
                },
                'id': {
                    'type': 'keyword',
                },
                'incorporation_date': {
                    'index': False,
                    'type': 'date',
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
                'registered_address_1': {
                    'index': False,
                    'type': 'text',
                },
                'registered_address_2': {
                    'index': False,
                    'type': 'text',
                },
                'registered_address_country': {
                    'properties': {
                        'id': {
                            'index': False,
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'registered_address_county': {
                    'index': False,
                    'type': 'text',
                },
                'registered_address_postcode': {
                    'type': 'text',
                    'fields': {
                        'trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                },
                'registered_address_town': {
                    'index': False,
                    'type': 'text',
                },
                'sic_code_1': {
                    'index': False,
                    'type': 'text',
                },
                'sic_code_2': {
                    'index': False,
                    'type': 'text',
                },
                'sic_code_3': {
                    'index': False,
                    'type': 'text',
                },
                'sic_code_4': {
                    'index': False,
                    'type': 'text',
                },
            },
        },
    }


@pytest.mark.django_db
def test_indexed_doc(setup_es):
    """Test the ES data of an indexed companies house company."""
    ch_company = CompaniesHouseCompanyFactory()

    doc = ESCompaniesHouseCompany.es_document(ch_company)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    setup_es.indices.refresh()

    indexed_ch_company = setup_es.get(
        index=ESCompaniesHouseCompany.get_write_index(),
        doc_type=CompaniesHouseCompanySearchApp.name,
        id=ch_company.pk,
    )

    assert indexed_ch_company == {
        '_index': ESCompaniesHouseCompany.get_target_index_name(),
        '_type': CompaniesHouseCompanySearchApp.name,
        '_id': str(ch_company.pk),
        '_version': indexed_ch_company['_version'],
        'found': True,
        '_source': {
            'id': str(ch_company.pk),
            'name': ch_company.name,
            'registered_address_1': ch_company.registered_address_1,
            'registered_address_2': ch_company.registered_address_2,
            'registered_address_town': ch_company.registered_address_town,
            'registered_address_county': ch_company.registered_address_county,
            'registered_address_postcode': ch_company.registered_address_postcode,
            'registered_address_country': {
                'id': str(ch_company.registered_address_country.pk),
                'name': ch_company.registered_address_country.name,
            },
            'company_number': ch_company.company_number,
            'company_category': ch_company.company_category,
            'company_status': ch_company.company_status,
            'sic_code_1': ch_company.sic_code_1,
            'sic_code_2': ch_company.sic_code_2,
            'sic_code_3': ch_company.sic_code_3,
            'sic_code_4': ch_company.sic_code_4,
            'incorporation_date': format_date_or_datetime(ch_company.incorporation_date),
        },
    }


def test_limited_get_search_by_entity_query():
    """Tests query generation for entity search."""
    query = get_search_by_entity_query(
        term='test',
        entity=ESCompaniesHouseCompany,
        filter_data={},
    )

    assert query.to_dict() == {
        'query': {
            'bool': {
                'must': [
                    {
                        'term': {
                            '_type': 'companieshousecompany',
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
                                            'name.trigram',
                                            'company_number',
                                            'registered_address_postcode.trigram',
                                            'name_trigram',
                                            'registered_address_postcode_trigram',
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
            'bool': {},
        },
        'sort': [
            '_score',
            'id',
        ],
    }
