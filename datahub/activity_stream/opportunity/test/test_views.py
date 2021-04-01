import pytest
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.core.test_utils import format_date_or_datetime
from datahub.investment.opportunity.test.factories import (
    CompleteLargeCapitalOpportunityFactory,
    LargeCapitalOpportunityFactory,
)


@pytest.mark.django_db
def test_large_capital_opportunity_activity(api_client):
    """
    Get a list of large capital opportunities and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    opportunity = LargeCapitalOpportunityFactory()
    response = hawk.get(
        api_client,
        get_url('api-v3:activity-stream:large-capital-opportunity'),
    )
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Large Capital Opportunity Activities Added',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/investment/large-capital-opportunity',
        'partOf': 'http://testserver/v3/activity-stream/investment/large-capital-opportunity',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubLargeCapitalOpportunity:{opportunity.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(opportunity.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubLargeCapitalOpportunity:{opportunity.id}',
                    'type': ['dit:LargeCapitalOpportunity'],
                    'dit:statusId': opportunity.status_id,
                    'startTime': format_date_or_datetime(opportunity.created_on),
                    'name': opportunity.name,
                    'attributedTo': [
                        {
                            'id':
                            f'dit:DataHubAdviser:{opportunity.lead_dit_relationship_manager.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                            opportunity.lead_dit_relationship_manager.contact_email
                            or opportunity.adviser.email,
                            'name': opportunity.lead_dit_relationship_manager.name,
                        },
                    ],
                    'url': opportunity.get_absolute_url(),
                    'description': '',
                    'dit:promoters': [],
                },
            },
        ],
    }


@pytest.mark.django_db
def test_complete_large_capital_opportunity_activity(api_client):
    """
    Get a list of large capital opportunities and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    opportunity = CompleteLargeCapitalOpportunityFactory()
    response = hawk.get(
        api_client,
        get_url('api-v3:activity-stream:large-capital-opportunity'),
    )

    def get_multiple_names(values):
        return [{'name': value.name} for value in values]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Large Capital Opportunity Activities Added',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/investment/large-capital-opportunity',
        'partOf': 'http://testserver/v3/activity-stream/investment/large-capital-opportunity',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubLargeCapitalOpportunity:{opportunity.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(opportunity.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubLargeCapitalOpportunity:{opportunity.id}',
                    'type': ['dit:LargeCapitalOpportunity'],
                    'startTime': format_date_or_datetime(opportunity.created_on),
                    'name': opportunity.name,
                    'description': opportunity.description,
                    'attributedTo': [
                        {
                            'id': (
                                f'dit:DataHub'
                                f'Adviser:{opportunity.lead_dit_relationship_manager.pk}'
                            ),
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                            opportunity.lead_dit_relationship_manager.contact_email
                            or opportunity.adviser.email,
                            'name': opportunity.lead_dit_relationship_manager.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{opportunity.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress': opportunity.created_by.contact_email
                            or opportunity.created_by.email,
                            'name': opportunity.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{opportunity.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': opportunity.created_by.dit_team.name,
                            },
                            'dit:DataHubLargeCapitalOpportunity:role': 'creator',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{opportunity.modified_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress': opportunity.modified_by.contact_email
                            or opportunity.modified_by.email,
                            'name': opportunity.modified_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{opportunity.modified_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': opportunity.modified_by.dit_team.name,
                            },
                            'dit:DataHubLargeCapitalOpportunity:role': 'modifier',
                        },
                    ],
                    'dit:promoters': [
                        {
                            'id': f'dit:DataHubCompany:{promoter.pk}',
                            'dit:dunsNumber': promoter.duns_number,
                            'dit:companiesHouseNumber': promoter.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': promoter.name,
                        }
                        for promoter in opportunity.promoters.order_by('pk')
                    ],
                    'url': opportunity.get_absolute_url(),
                    'dit:statusId': opportunity.status_id,
                    'dit:requiredChecksConducted': {
                        'name': opportunity.required_checks_conducted.name,
                    },
                    'dit:requiredChecksConductedId':
                    opportunity.required_checks_conducted_id,
                    'dit:requiredChecksConductedOn':
                    opportunity.required_checks_conducted_on.strftime(
                        '%Y-%m-%d',
                    ),
                    'dit:requiredChecksConductedBy': [
                        {
                            'id': 'dit:DataHubAdviser:'
                            f'{opportunity.required_checks_conducted_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                            opportunity.required_checks_conducted_by.contact_email
                            or opportunity.required_checks_conducted_by.email,
                            'name': opportunity.required_checks_conducted_by.name,
                            'dit:team': {
                                'id': 'dit:DataHubTeam:'
                                f'{opportunity.required_checks_conducted_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': opportunity.required_checks_conducted_by.dit_team.name,
                            },
                        },
                    ],
                    'dit:opportunityValueType': {
                        'name': opportunity.opportunity_value_type.name,
                    },
                    'dit:estimatedReturnRateId': str(
                        opportunity.estimated_return_rate.id,
                    ),
                    'dit:assetClasses': get_multiple_names(
                        opportunity.asset_classes.all(),
                    ),
                    'dit:investmentTypes': get_multiple_names(
                        opportunity.investment_types.all(),
                    ),
                    'dit:constructionRisks': get_multiple_names(
                        opportunity.construction_risks.all(),
                    ),
                    'dit:timeHorizons': get_multiple_names(
                        opportunity.time_horizons.all(),
                    ),
                    'dit:sourcesOfFunding': get_multiple_names(
                        opportunity.sources_of_funding.all(),
                    ),
                    'dit:reasonsForAbandonment': get_multiple_names(
                        opportunity.reasons_for_abandonment.all(),
                    ),
                    'dit:ukRegionLocations': get_multiple_names(
                        opportunity.uk_region_locations.all(),
                    ),
                    'dit:totalInvestmentSought': float(
                        opportunity.total_investment_sought,
                    ),
                    'dit:currentInvestmentSecured': float(
                        opportunity.current_investment_secured,
                    ),
                    'dit:opportunityValue': float(opportunity.opportunity_value),
                },
            },
        ],
    }
