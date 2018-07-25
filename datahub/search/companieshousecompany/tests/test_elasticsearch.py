import pytest
from elasticsearch_dsl import Mapping

from datahub.company.test.factories import (
    CompaniesHouseCompanyFactory
)
from datahub.core.test_utils import format_date_or_datetime
from .. import CompaniesHouseCompanySearchApp
from ..models import CompaniesHouseCompany as ESCompaniesHouseCompany
from ... import elasticsearch

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
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'company_number': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'company_status': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'id': {
                    'type': 'keyword'
                },
                'incorporation_date': {
                    'type': 'date'
                },
                'name': {
                    'copy_to': ['name_keyword', 'name_trigram'],
                    'fielddata': True,
                    'type': 'text'
                },
                'name_keyword': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'name_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text'
                },
                'registered_address_1': {
                    'type': 'text'
                },
                'registered_address_2': {
                    'type': 'text'
                },
                'registered_address_country': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {
                            'type': 'keyword'
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text'
                        }
                    },
                    'type': 'nested'
                },
                'registered_address_county': {
                    'type': 'text'
                },
                'registered_address_postcode': {
                    'copy_to': ['registered_address_postcode_trigram'],
                    'type': 'text'
                },
                'registered_address_postcode_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text'
                },
                'registered_address_town': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text'
                },
                'sic_code_1': {
                    'type': 'text'
                },
                'sic_code_2': {
                    'type': 'text'
                },
                'sic_code_3': {
                    'type': 'text'
                },
                'sic_code_4': {
                    'type': 'text'
                },
                'uri': {
                    'type': 'text'
                }
            }
        }
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
        id=ch_company.pk
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
                'name': ch_company.registered_address_country.name
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
    }
