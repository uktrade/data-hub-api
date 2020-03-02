import freezegun
import pytest
from elasticsearch_dsl import Mapping

from datahub.company.test.factories import CompanyFactory
from datahub.investment.investor_profile.test.factories import LargeCapitalInvestorProfileFactory
from datahub.search import elasticsearch
from datahub.search.large_investor_profile import LargeInvestorProfileSearchApp
from datahub.search.large_investor_profile.models import (
    LargeInvestorProfile as ESLargeInvestorProfile,
)


pytestmark = pytest.mark.django_db


def test_mapping(es):
    """Test the ES mapping for a large capital investor profile."""
    mapping = Mapping.from_es(
        LargeInvestorProfileSearchApp.es_model.get_write_index(),
        LargeInvestorProfileSearchApp.name,
    )
    assert mapping.to_dict() == {
        'large-investor-profile': {
            'properties': {
                '_document_type': {
                    'type': 'keyword',
                },
                'asset_classes_of_interest': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'construction_risks': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'country_of_origin': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'fields': {
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'created_by': {
                    'properties': {
                        'dit_team': {
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
                        'first_name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'id': {
                            'type': 'keyword',
                        },
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
                'created_on': {
                    'type': 'date',
                },
                'deal_ticket_sizes': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'desired_deal_roles': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'global_assets_under_management': {
                    'type': 'long',
                },
                'id': {
                    'type': 'keyword',
                },
                'investable_capital': {
                    'type': 'long',
                },
                'investment_types': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'investor_company': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'fields': {
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                                'keyword': {
                                    'normalizer': 'lowercase_asciifolding_normalizer',
                                    'type': 'keyword',
                                },
                            },
                            'type': 'text',
                        },
                        'trading_names': {
                            'fields': {
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'investor_description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'investor_type': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'minimum_equity_percentage': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'minimum_return_rate': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'modified_on': {
                    'type': 'date',
                },
                'notes_on_locations': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'other_countries_being_considered': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'fields': {
                                'trigram': {
                                    'analyzer': 'trigram_analyzer',
                                    'type': 'text',
                                },
                            },
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'required_checks_conducted': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'restrictions': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'time_horizons': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'uk_region_locations': {
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'index': False,
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
            },
            'dynamic': 'false',
        },
    }


@freezegun.freeze_time('2019-01-01')
def test_indexed_doc(es):
    """Test the ES data of an Large investor profile."""
    investor_company = CompanyFactory()

    large_investor_profile = LargeCapitalInvestorProfileFactory(
        investor_company=investor_company,
    )

    doc = ESLargeInvestorProfile.es_document(large_investor_profile)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    es.indices.refresh()

    indexed_large_investor_profile = es.get(
        index=ESLargeInvestorProfile.get_write_index(),
        doc_type=LargeInvestorProfileSearchApp.name,
        id=large_investor_profile.pk,
    )

    assert indexed_large_investor_profile['_id'] == str(large_investor_profile.pk)
    assert indexed_large_investor_profile['_source'] == {
        '_document_type': LargeInvestorProfileSearchApp.name,
        'id': str(large_investor_profile.pk),
        'asset_classes_of_interest': [],
        'country_of_origin': {
            'id': str(large_investor_profile.country_of_origin.pk),
            'name': str(large_investor_profile.country_of_origin.name),
        },
        'investor_company': {
            'id': str(investor_company.pk),
            'name': str(investor_company.name),
            'trading_names': investor_company.trading_names,
        },
        'created_by': None,
        'investor_type': None,
        'required_checks_conducted': None,
        'deal_ticket_sizes': [],
        'investment_types': [],
        'minimum_return_rate': None,
        'time_horizons': [],
        'restrictions': [],
        'construction_risks': [],
        'minimum_equity_percentage': None,
        'desired_deal_roles': [],
        'uk_region_locations': [],
        'other_countries_being_considered': [],
        'investable_capital': None,
        'investor_description': '',
        'created_on': '2019-01-01T00:00:00+00:00',
        'notes_on_locations': '',
        'global_assets_under_management': None,
        'modified_on': '2019-01-01T00:00:00+00:00',
    }
