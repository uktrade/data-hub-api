import pytest
from opensearch_dsl import Mapping

from datahub.core.constants import Country
from datahub.search.investment.models import InvestmentProject as SearchInvestmentProject
from datahub.search.query_builder import (
    get_basic_search_query,
    get_search_by_entities_query,
    limit_search_query,
)


def test_mapping(opensearch):
    """Test the OpenSearch mapping for an investment project."""
    mapping = Mapping.from_opensearch(
        SearchInvestmentProject.get_write_index(),
    )

    assert mapping.to_dict() == {
        'dynamic': 'false',
        'properties': {
            '_document_type': {
                'type': 'keyword',
            },
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
            'client_requirements': {
                'type': 'text',
                'index': False,
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
                        'type': 'keyword',
                        'index': False,
                    },
                    'name': {
                        'type': 'text',
                        'index': False,
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
            'gross_value_added': {'type': 'double'},
            'id': {'type': 'keyword'},
            'incomplete_fields': {'type': 'text'},
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
            'latest_interaction': {
                'properties': {
                    'id': {'type': 'keyword'},
                    'date': {'type': 'date'},
                    'subject': {
                        'index': False,
                        'type': 'text',
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
                'type': 'text',
                'index': False,
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
            'project_code': {
                'normalizer': 'lowercase_asciifolding_normalizer',
                'type': 'keyword',
                'fields': {
                    'trigram': {
                        'analyzer': 'trigram_analyzer',
                        'type': 'text',
                    },
                },
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
            'proposal_deadline': {'type': 'date'},
            'quotable_as_public_case_study': {'type': 'boolean'},
            'r_and_d_budget': {'type': 'boolean'},
            'reason_abandoned': {
                'type': 'text',
                'index': False,
            },
            'reason_delayed': {
                'type': 'text',
                'index': False,
            },
            'reason_lost': {
                'type': 'text',
                'index': False,
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
                        'type': 'text',
                        'index': False,
                    },
                    'id': {
                        'type': 'keyword',
                        'index': False,
                    },
                    'last_name': {
                        'type': 'text',
                        'index': False,
                    },
                    'name': {
                        'type': 'text',
                        'index': False,
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
            'site_address_is_company_address': {'type': 'boolean'},
            'some_new_jobs': {'type': 'boolean'},
            'specific_programmes': {
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
            'total_investment': {'type': 'double'},
            'uk_company': {
                'properties': {
                    'id': {'type': 'keyword'},
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
            'one_list_group_global_account_manager': {
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
                        'fields': {
                            'keyword': {
                                'normalizer': 'lowercase_asciifolding_normalizer',
                                'type': 'keyword',
                            },
                            'trigram': {'analyzer': 'trigram_analyzer', 'type': 'text'},
                        },
                        'type': 'text',
                    },
                },
                'type': 'object',
            },
        },
    }


@pytest.mark.django_db
def test_get_basic_search_query():
    """Tests basic search query."""
    expected_query = {
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
                                'advisers',
                                'companies.name',
                                'companies.name.trigram',
                                'company.name',
                                'company.name.trigram',
                                'company_number',
                                'contact.name',
                                'contact.name.trigram',
                                'contacts.id',
                                'contacts.name',
                                'contacts.name.trigram',
                                'country.trigram',
                                'created_by',
                                'dit_participants.adviser.name',
                                'dit_participants.adviser.name.trigram',
                                'dit_participants.team.name',
                                'dit_participants.team.name.trigram',
                                'due_date',
                                'email',
                                'event.name',
                                'event.name.trigram',
                                'event_type.name',
                                'event_type.name.trigram',
                                'export_segment',
                                'export_sub_segment',
                                'first_name',
                                'first_name.trigram',
                                'full_telephone_number',
                                'id',
                                'interaction.subject',
                                'interaction.subject.trigram',
                                'investor_company.name',
                                'investor_company.name.trigram',
                                'is_active',
                                'job_title',
                                'job_title.trigram',
                                'last_name',
                                'last_name.trigram',
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
                                'status',
                                'subject',
                                'subject.english',
                                'subject.trigram',
                                'subtotal_cost.keyword',
                                'teams.name',
                                'teams.name.trigram',
                                'title',
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
                            '_document_type': 'investment_project',
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

    query = get_basic_search_query(
        SearchInvestmentProject,
        'test',
        offset=5,
        limit=5,
    )

    assert query.to_dict() == expected_query


@pytest.mark.django_db
def test_limited_get_search_by_entity_query():
    """Tests search by entity."""
    date = '2017-06-13T09:44:31.062870'
    filter_data = {
        'investor_company_country.id': ['80756b9a-5d95-e211-a939-e4115bead28a'],
        'estimated_land_date_after': date,
        'estimated_land_date_before': date,
    }
    query = get_search_by_entities_query(
        [SearchInvestmentProject],
        term='test',
        filter_data=filter_data,
    )
    query = limit_search_query(
        query,
        offset=5,
        limit=5,
    )
    investment_query = Country.united_kingdom.value.id
    assert query.to_dict() == {
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
                                },
                                {
                                    'multi_match': {
                                        'query': 'test',
                                        'fields': (
                                            'id',
                                            'name',
                                            'name.trigram',
                                            'uk_company.name',
                                            'uk_company.name.trigram',
                                            'investor_company.name',
                                            'investor_company.name.trigram',
                                            'project_code',
                                            'sector.name',
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
                                                        'query': investment_query,
                                                        'operator': 'and',
                                                    },
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
