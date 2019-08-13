import pytest
from elasticsearch_dsl import Mapping

from datahub.company.test.factories import CompaniesHouseCompanyFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.search import elasticsearch
from datahub.search.companieshousecompany import CompaniesHouseCompanySearchApp
from datahub.search.companieshousecompany.models import (
    CompaniesHouseCompany as ESCompaniesHouseCompany,
)

pytestmark = pytest.mark.django_db


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
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'company_number': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'company_status': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'id': {
                    'type': 'keyword',
                },
                'incorporation_date': {
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
                    'type': 'text',
                },
                'registered_address_2': {
                    'type': 'text',
                },
                'registered_address_country': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'registered_address_county': {
                    'type': 'text',
                },
                'registered_address_postcode': {
                    'type': 'text',
                },
                'registered_address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
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
                                'name': {'index': False, 'type': 'text'},
                            },
                        },
                    },
                },
                'sic_code_1': {
                    'type': 'text',
                },
                'sic_code_2': {
                    'type': 'text',
                },
                'sic_code_3': {
                    'type': 'text',
                },
                'sic_code_4': {
                    'type': 'text',
                },
                'uri': {
                    'type': 'text',
                },
            },
        },
    }


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

    assert indexed_ch_company['_id'] == str(ch_company.pk)
    assert indexed_ch_company['_source'] == {
        'id': str(ch_company.pk),
        'name': ch_company.name,
        'registered_address': {
            'line_1': ch_company.registered_address_1,
            'line_2': ch_company.registered_address_2,
            'town': ch_company.registered_address_town,
            'county': ch_company.registered_address_county,
            'postcode': ch_company.registered_address_postcode,
            'country': {
                'id': str(ch_company.registered_address_country.pk),
                'name': ch_company.registered_address_country.name,
            },
        },
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
        'uri': ch_company.uri,
        'incorporation_date': format_date_or_datetime(ch_company.incorporation_date),
    }
