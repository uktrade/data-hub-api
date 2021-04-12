import freezegun
import pytest
from elasticsearch_dsl import Mapping

from datahub.investment.opportunity.test.constants import (
    OpportunityStatus as OpportunityStatusConstant,
    OpportunityType as OpportunityTypeConstant,
)
from datahub.investment.opportunity.test.factories import LargeCapitalOpportunityFactory
from datahub.search import elasticsearch
from datahub.search.large_capital_opportunity import LargeCapitalOpportunitySearchApp
from datahub.search.large_capital_opportunity.models import (
    LargeCapitalOpportunity as ESLargeCapitalOpportunity,
)

pytestmark = pytest.mark.django_db


def test_mapping(es):
    """Test the ES mapping for a large capital opportunity."""
    mapping = Mapping.from_es(
        LargeCapitalOpportunitySearchApp.es_model.get_write_index(),
    )
    assert mapping.to_dict() == {
        'properties': {
            '_document_type': {
                'type': 'keyword',
            },
            'asset_classes': {
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
                    'id': {
                        'type': 'keyword',
                    },
                    'last_name': {
                        'normalizer': 'lowercase_asciifolding_normalizer',
                        'type': 'keyword',
                    },
                    'name': {
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
                        'type': 'text',
                    },
                },
                'type': 'object',
            },
            'created_on': {
                'type': 'date',
            },
            'current_investment_secured': {
                'type': 'long',
            },
            'description': {
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
                'type': 'text',
            },
            'dit_support_provided': {'type': 'boolean'},
            'estimated_return_rate': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'id': {'type': 'keyword'},
            'investment_projects': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'investment_types': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'lead_dit_relationship_manager': {
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
                        'type': 'text',
                    },
                },
                'type': 'object',
            },
            'modified_on': {'type': 'date'},
            'name': {
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
                'type': 'text',
            },
            'opportunity_value': {'type': 'long'},
            'opportunity_value_type': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'other_dit_contacts': {
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
                        'type': 'text',
                    },
                },
                'type': 'object',
            },
            'promoters': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {
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
            'reasons_for_abandonment': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'required_checks_conducted': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'required_checks_conducted_by': {
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
                        'type': 'text',
                    },
                },
                'type': 'object',
            },
            'required_checks_conducted_on': {'type': 'date'},
            'sources_of_funding': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'status': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'time_horizons': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'total_investment_sought': {'type': 'long'},
            'type': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
            'uk_region_locations': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'name': {'index': False, 'type': 'keyword'},
                },
                'type': 'object',
            },
        },
        'dynamic': 'false',
    }


@freezegun.freeze_time('2019-01-01')
def test_indexed_doc(es):
    """Test the ES data of a large capital opportunity."""
    opportunity = LargeCapitalOpportunityFactory(
        lead_dit_relationship_manager=None,
    )

    doc = ESLargeCapitalOpportunity.es_document(opportunity)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)

    es.indices.refresh()

    indexed_large_capital_opportunity = es.get(
        index=ESLargeCapitalOpportunity.get_write_index(),
        id=opportunity.pk,
    )

    assert indexed_large_capital_opportunity['_id'] == str(opportunity.pk)
    assert indexed_large_capital_opportunity['_source'] == {
        '_document_type': LargeCapitalOpportunitySearchApp.name,
        'id': str(opportunity.pk),
        'type': {
            'id': str(OpportunityTypeConstant.large_capital.value.id),
            'name': OpportunityTypeConstant.large_capital.value.name,
        },
        'status': {
            'id': str(OpportunityStatusConstant.abandoned.value.id),
            'name': OpportunityStatusConstant.abandoned.value.name,
        },
        'created_by': None,
        'uk_region_locations': [],
        'promoters': [],
        'required_checks_conducted': None,
        'required_checks_conducted_by': None,
        'lead_dit_relationship_manager': None,
        'other_dit_contacts': [],
        'asset_classes': [],
        'opportunity_value': None,
        'opportunity_value_type': None,
        'investment_types': [],
        'construction_risks': [],
        'estimated_return_rate': None,
        'time_horizons': [],
        'investment_projects': [],
        'sources_of_funding': [],
        'reasons_for_abandonment': [],
        'total_investment_sought': None,
        'current_investment_secured': None,
        'modified_on': '2019-01-01T00:00:00+00:00',
        'created_on': '2019-01-01T00:00:00+00:00',
        'description': '',
        'required_checks_conducted_on': None,
        'name': '',
        'dit_support_provided': False,
    }
