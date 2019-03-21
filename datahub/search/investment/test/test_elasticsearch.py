from elasticsearch_dsl import Mapping

from datahub.search.investment.models import InvestmentProject as ESInvestmentProject
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entity_query,
    limit_search_query,
)


def test_mapping(setup_es):
    """Test the ES mapping for an investment project."""
    mapping = Mapping.from_es(
        ESInvestmentProject.get_write_index(),
        ESInvestmentProject._doc_type.name,
    )

    assert mapping.to_dict() == {
        'investment_project': {
            'dynamic': 'false',
            'properties': {
                'actual_land_date': {'type': 'date'},
                'actual_uk_regions': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'address_1': {'type': 'text'},
                'address_2': {'type': 'text'},
                'address_postcode': {'type': 'text'},
                'address_town': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'allow_blank_estimated_land_date': {
                    'index': False,
                    'type': 'boolean',
                },
                'allow_blank_possible_uk_regions': {
                    'index': False,
                    'type': 'boolean',
                },
                'anonymous_description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'approved_commitment_to_invest': {'type': 'boolean'},
                'approved_fdi': {'type': 'boolean'},
                'approved_good_value': {'type': 'boolean'},
                'approved_high_value': {'type': 'boolean'},
                'approved_landed': {'type': 'boolean'},
                'approved_non_fdi': {'type': 'boolean'},
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
                'associated_non_fdi_r_and_d_project': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                        'project_code': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'average_salary': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'business_activities': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'client_cannot_provide_foreign_investment': {'type': 'boolean'},
                'client_cannot_provide_total_investment': {'type': 'boolean'},
                'client_contacts': {
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
                            'copy_to': ['client_contacts.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'client_relationship_manager': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['client_relationship_manager.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'client_requirements': {
                    'fields': {
                        'keyword': {
                            'ignore_above': 256,
                            'type': 'keyword',
                        },
                    },
                    'type': 'text',
                },
                'comments': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'country_investment_originates_from': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'country_lost_to': {
                    'properties': {
                        'id': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
                                },
                            },
                            'type': 'text',
                        },
                        'name': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['created_by.name_trigram'],
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
                'date_abandoned': {'type': 'date'},
                'date_lost': {'type': 'date'},
                'delivery_partners': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'estimated_land_date': {'type': 'date'},
                'export_revenue': {'type': 'boolean'},
                'fdi_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'fdi_value': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'foreign_equity_investment': {'type': 'double'},
                'government_assistance': {'type': 'boolean'},
                'id': {'type': 'keyword'},
                'intermediate_company': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'investment_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'investor_company': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['investor_company.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'investor_company_country': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'investor_type': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'level_of_involvement': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'level_of_involvement_simplified': {'type': 'keyword'},
                'likelihood_to_land': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
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
                'new_tech_to_uk': {'type': 'boolean'},
                'non_fdi_r_and_d_budget': {'type': 'boolean'},
                'number_new_jobs': {'type': 'integer'},
                'number_safeguarded_jobs': {'type': 'long'},
                'other_business_activity': {
                    'fields': {
                        'keyword': {
                            'ignore_above': 256,
                            'type': 'keyword',
                        },
                    },
                    'type': 'text',
                },
                'project_arrived_in_triage_on': {'type': 'date'},
                'project_assurance_adviser': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['project_assurance_adviser.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'project_code': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'copy_to': ['project_code_trigram'],
                    'type': 'keyword',
                },
                'project_code_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'project_manager': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['project_manager.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'proposal_deadline': {'type': 'date'},
                'quotable_as_public_case_study': {'type': 'boolean'},
                'r_and_d_budget': {'type': 'boolean'},
                'reason_abandoned': {
                    'fields': {
                        'keyword': {
                            'ignore_above': 256,
                            'type': 'keyword',
                        },
                    },
                    'type': 'text',
                },
                'reason_delayed': {
                    'fields': {
                        'keyword': {
                            'ignore_above': 256,
                            'type': 'keyword',
                        },
                    },
                    'type': 'text',
                },
                'reason_lost': {
                    'fields': {
                        'keyword': {
                            'ignore_above': 256,
                            'type': 'keyword',
                        },
                    },
                    'type': 'text',
                },
                'referral_source_activity': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'referral_source_activity_event': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'referral_source_activity_marketing': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'referral_source_activity_website': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'referral_source_adviser': {
                    'properties': {
                        'first_name': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
                                },
                            },
                            'type': 'text',
                        },
                        'id': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
                                },
                            },
                            'type': 'text',
                        },
                        'last_name': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
                                },
                            },
                            'type': 'text',
                        },
                        'name': {
                            'fields': {
                                'keyword': {
                                    'ignore_above': 256,
                                    'type': 'keyword',
                                },
                            },
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
                'site_decided': {'type': 'boolean'},
                'some_new_jobs': {'type': 'boolean'},
                'specific_programme': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'stage': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'status': {
                    'normalizer': 'lowercase_asciifolding_normalizer',
                    'type': 'keyword',
                },
                'team_members': {
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
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['team_members.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'total_investment': {'type': 'double'},
                'uk_company': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'copy_to': ['uk_company.name_trigram'],
                            'type': 'keyword',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'uk_company_decided': {'type': 'boolean'},
                'uk_region_locations': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'normalizer': 'lowercase_asciifolding_normalizer',
                            'type': 'keyword',
                        },
                    },
                    'type': 'object',
                },
                'will_new_jobs_last_two_years': {'type': 'boolean'},
            },
        },
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query(
        ESInvestmentProject, 'test', offset=5, limit=5,
    )

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
                                'address.country.name.trigram',
                                'address.postcode.trigram',
                                'address_country.name_trigram',
                                'address_postcode_trigram',
                                'company.name',
                                'company.name_trigram',
                                'company_number',
                                'contact.name',
                                'contact.name_trigram',
                                'contacts.name',
                                'contacts.name.trigram',
                                'dit_participants.adviser.name',
                                'dit_participants.adviser.name.trigram',
                                'dit_participants.team.name',
                                'dit_participants.team.name.trigram',
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
                                'registered_address.country.name.trigram',
                                'registered_address.postcode.trigram',
                                'related_programmes.name',
                                'related_programmes.name_trigram',
                                'subject_english',
                                'subtotal_cost_string',
                                'teams.name',
                                'teams.name_trigram',
                                'total_cost_string',
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
                            '_type': 'investment_project',
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
        'investor_company_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'estimated_land_date_after': date,
        'estimated_land_date_before': date,
    }
    query = get_search_by_entity_query(
        ESInvestmentProject,
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
                            '_type': 'investment_project',
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
                                            'uk_company.name',
                                            'uk_company.name_trigram',
                                            'investor_company.name',
                                            'investor_company.name_trigram',
                                            'project_code_trigram',
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
                                                    'investor_company_country.id': {
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
                                            'gte': '2017-06-13T09:44:31.062870',
                                            'lte': '2017-06-13T09:44:31.062870',
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
