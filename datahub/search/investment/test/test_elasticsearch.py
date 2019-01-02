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
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'address_1': {'type': 'text'},
                'address_2': {'type': 'text'},
                'address_postcode': {'type': 'text'},
                'address_town': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
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
                    'include_in_parent': True,
                    'properties': {
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['archived_by.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'archived_on': {'type': 'date'},
                'archived_reason': {'type': 'text'},
                'associated_non_fdi_r_and_d_project': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'project_code': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'average_salary': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'business_activities': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'client_cannot_provide_foreign_investment': {'type': 'boolean'},
                'client_cannot_provide_total_investment': {'type': 'boolean'},
                'client_contacts': {
                    'include_in_parent': True,
                    'properties': {
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['client_contacts.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'client_relationship_manager': {
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text',
                                },
                            },
                            'type': 'nested',
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['client_relationship_manager.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
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
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
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
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text',
                                },
                            },
                            'type': 'nested',
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['created_by.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'created_on': {'type': 'date'},
                'date_abandoned': {'type': 'date'},
                'date_lost': {'type': 'date'},
                'delivery_partners': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'description': {
                    'analyzer': 'english_analyzer',
                    'type': 'text',
                },
                'estimated_land_date': {'type': 'date'},
                'export_revenue': {'type': 'boolean'},
                'fdi_type': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'fdi_value': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'foreign_equity_investment': {'type': 'double'},
                'government_assistance': {'type': 'boolean'},
                'id': {'type': 'keyword'},
                'intermediate_company': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'investment_type': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'investor_company': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['investor_company.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'investor_company_country': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'investor_type': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'level_of_involvement': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'level_of_involvement_simplified': {'type': 'keyword'},
                'likelihood_to_land': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'object',
                },
                'modified_on': {'type': 'date'},
                'name': {
                    'copy_to': [
                        'name_keyword',
                        'name_trigram',
                    ],
                    'fielddata': True,
                    'type': 'text',
                },
                'name_keyword': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'name_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
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
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text',
                                },
                            },
                            'type': 'nested',
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['project_assurance_adviser.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'project_code': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'copy_to': ['project_code_trigram'],
                    'fielddata': True,
                    'type': 'text',
                },
                'project_code_trigram': {
                    'analyzer': 'trigram_analyzer',
                    'type': 'text',
                },
                'project_manager': {
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text',
                                },
                            },
                            'type': 'nested',
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['project_manager.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
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
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'referral_source_activity_event': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'referral_source_activity_marketing': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'referral_source_activity_website': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
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
                    'include_in_parent': True,
                    'properties': {
                        'ancestors': {
                            'include_in_parent': True,
                            'properties': {'id': {'type': 'keyword'}},
                            'type': 'nested',
                        },
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'site_decided': {'type': 'boolean'},
                'some_new_jobs': {'type': 'boolean'},
                'specific_programme': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'stage': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'status': {
                    'analyzer': 'lowercase_keyword_analyzer',
                    'fielddata': True,
                    'type': 'text',
                },
                'team_members': {
                    'include_in_parent': True,
                    'properties': {
                        'dit_team': {
                            'include_in_parent': True,
                            'properties': {
                                'id': {'type': 'keyword'},
                                'name': {
                                    'analyzer': 'lowercase_keyword_analyzer',
                                    'fielddata': True,
                                    'type': 'text',
                                },
                            },
                            'type': 'nested',
                        },
                        'first_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'id': {'type': 'keyword'},
                        'last_name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['team_members.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'total_investment': {'type': 'double'},
                'uk_company': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'copy_to': ['uk_company.name_trigram'],
                            'fielddata': True,
                            'type': 'text',
                        },
                        'name_trigram': {
                            'analyzer': 'trigram_analyzer',
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'uk_company_decided': {'type': 'boolean'},
                'uk_region_locations': {
                    'include_in_parent': True,
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'analyzer': 'lowercase_keyword_analyzer',
                            'fielddata': True,
                            'type': 'text',
                        },
                    },
                    'type': 'nested',
                },
                'will_new_jobs_last_two_years': {'type': 'boolean'},
            },
        },
    }


def test_get_basic_search_query():
    """Tests basic search query."""
    query = get_basic_search_query(
        'test', entities=(ESInvestmentProject,), offset=5, limit=5,
    )

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
                                'trading_name',
                                'trading_name_trigram',
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
        'address_town': ['Woodside'],
        'trading_address_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'estimated_land_date_after': date,
        'estimated_land_date_before': date,
    }
    query = get_search_by_entity_query(
        term='test',
        filter_data=filter_data,
        entity=ESInvestmentProject,
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
                            'should': [
                                {
                                    'match_phrase': {
                                        'trading_address_country.id':
                                            '80756b9a-5d95-e211-a939-e4115bead28a',
                                    },
                                },
                            ],
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
