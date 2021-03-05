import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.core.test_utils import format_date_or_datetime
from datahub.investment.investor_profile.test.factories import (
    CompleteLargeCapitalInvestorProfileFactory,
    LargeCapitalInvestorProfileFactory,
)


@pytest.mark.django_db
def test_large_capital_investor_profile_activity(api_client):
    """
    Get a list of large capital investor profiles and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    investor_profile = LargeCapitalInvestorProfileFactory()
    response = hawk.get(
        api_client, get_url('api-v3:activity-stream:large-capital-investor-profiles'),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Large Capital Investor Profile Activities',
        'type': 'OrderedCollectionPage',
        'id':
            'http://testserver/v3/activity-stream/investment/large-capital-investor-profiles',
        'partOf':
            'http://testserver/v3/activity-stream/investment/large-capital-investor-profiles',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubLargeCapitalInvestorProfile:{investor_profile.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(investor_profile.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubLargeCapitalInvestorProfile:{investor_profile.id}',
                    'type': ['dit:LargeCapitalInvestorProfile'],
                    'startTime': format_date_or_datetime(investor_profile.created_on),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{investor_profile.investor_company.pk}',
                            'dit:dunsNumber': investor_profile.investor_company.duns_number,
                            'dit:companiesHouseNumber':
                                investor_profile.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': investor_profile.investor_company.name,
                        },
                    ],
                    'dit:countryOfOrigin': {'name': investor_profile.country_of_origin.name},
                    'url': investor_profile.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_complete_large_capital_investor_profile_activity(api_client):
    """
    Get a list of complete large capital investor profiles and test the returned JSON
    is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    investor_profile = CompleteLargeCapitalInvestorProfileFactory()
    response = hawk.get(
        api_client, get_url('api-v3:activity-stream:large-capital-investor-profiles'),
    )

    def get_multiple_names(values):
        return [{'name': value.name} for value in values]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Large Capital Investor Profile Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/investment/large-capital-investor-profiles',
        'partOf':
            'http://testserver/v3/activity-stream/investment/large-capital-investor-profiles',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubLargeCapitalInvestorProfile:{investor_profile.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(investor_profile.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubLargeCapitalInvestorProfile:{investor_profile.id}',
                    'type': ['dit:LargeCapitalInvestorProfile'],
                    'startTime': format_date_or_datetime(investor_profile.created_on),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{investor_profile.investor_company.pk}',
                            'dit:dunsNumber': investor_profile.investor_company.duns_number,
                            'dit:companiesHouseNumber':
                                investor_profile.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': investor_profile.investor_company.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{investor_profile.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                investor_profile.created_by.contact_email
                                or investor_profile.created_by.email,
                            'name': investor_profile.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{investor_profile.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': investor_profile.created_by.dit_team.name,
                            },
                            'dit:DataHubLargeCapitalInvestorProfile:role': 'creator',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{investor_profile.modified_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                investor_profile.modified_by.contact_email
                                or investor_profile.modified_by.email,
                            'name': investor_profile.modified_by.name,
                            'dit:team': {
                                'id':
                                    f'dit:DataHubTeam:{investor_profile.modified_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': investor_profile.modified_by.dit_team.name,
                            },
                            'dit:DataHubLargeCapitalInvestorProfile:role': 'modifier',
                        },
                    ],
                    'url': investor_profile.get_absolute_url(),
                    'dit:assetClassesOfInterest': get_multiple_names(
                        investor_profile.asset_classes_of_interest.all(),
                    ),
                    'dit:constructionRisks': get_multiple_names(
                        investor_profile.construction_risks.all(),
                    ),
                    'dit:countryOfOrigin': {'name': investor_profile.country_of_origin.name},
                    'dit:dealTicketSizes': get_multiple_names(
                        investor_profile.deal_ticket_sizes.all(),
                    ),
                    'dit:desiredDealRoles': get_multiple_names(
                        investor_profile.desired_deal_roles.all(),
                    ),
                    'dit:globalAssetsUnderManagement':
                        investor_profile.global_assets_under_management,
                    'dit:investableCapital': investor_profile.investable_capital,
                    'dit:investmentTypes': get_multiple_names(
                        investor_profile.investment_types.all(),
                    ),
                    'dit:investorDescription': investor_profile.investor_description,
                    'dit:investorType': {'name': investor_profile.investor_type.name},
                    'dit:minimumEquityPercentage': {
                        'name': investor_profile.minimum_equity_percentage.name,
                    },
                    'dit:minimumReturnRate': {'name': investor_profile.minimum_return_rate.name},
                    'dit:notesOnLocations': investor_profile.notes_on_locations,
                    'dit:otherCountriesBeingConsidered': get_multiple_names(
                        investor_profile.other_countries_being_considered.all(),
                    ),
                    'dit:requiredChecksConducted': {
                        'name': investor_profile.required_checks_conducted.name,
                    },
                    'dit:requiredChecksConductedBy': [{
                        'id': 'dit:DataHubAdviser:'
                        f'{investor_profile.required_checks_conducted_by.pk}',
                        'type': ['Person', 'dit:Adviser'],
                        'dit:emailAddress':
                            investor_profile.required_checks_conducted_by.contact_email
                            or investor_profile.required_checks_conducted_by.email,
                        'name': investor_profile.required_checks_conducted_by.name,
                        'dit:team': {
                            'id': 'dit:DataHubTeam:'
                            f'{investor_profile.required_checks_conducted_by.dit_team.pk}',
                            'type': ['Group', 'dit:Team'],
                            'name': investor_profile.required_checks_conducted_by.dit_team.name,
                        },
                    }],
                    'dit:requiredChecksConductedOn':
                        investor_profile.required_checks_conducted_on.strftime('%Y-%m-%d'),
                    'dit:restrictions': get_multiple_names(
                        investor_profile.restrictions.all(),
                    ),
                    'dit:timeHorizons': get_multiple_names(
                        investor_profile.time_horizons.all(),
                    ),
                    'dit:ukRegionLocations': get_multiple_names(
                        investor_profile.uk_region_locations.all(),
                    ),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_investor_profiles_ordering(api_client):
    """
    Test that the investor profiles are ordered by ('modified_on', 'pk')
    """
    investor_profiles = []

    # We create 2 profiles with the same modified_on time
    with freeze_time():
        investor_profiles += LargeCapitalInvestorProfileFactory.create_batch(2)
    investor_profiles += LargeCapitalInvestorProfileFactory.create_batch(8)
    response = hawk.get(
        api_client, get_url('api-v3:activity-stream:large-capital-investor-profiles'),
    )
    assert response.status_code == status.HTTP_200_OK

    sorted_investor_profile_ids = [
        f'dit:DataHubLargeCapitalInvestorProfile:{obj.pk}'
        for obj in sorted(investor_profiles, key=lambda obj: (obj.modified_on, obj.pk))
    ]
    response_investor_profile_ids = [
        item['object']['id']
        for item in response.json()['orderedItems']
    ]
    assert sorted_investor_profile_ids == response_investor_profile_ids
