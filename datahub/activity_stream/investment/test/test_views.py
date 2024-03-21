import datetime

import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.core import constants
from datahub.core.test_utils import format_date_or_datetime
from datahub.investment.project.test.factories import (
    AssignPMInvestmentProjectFactory,
    InvestmentProjectFactory,
    VerifyWinInvestmentProjectFactory,
)


@pytest.mark.django_db
def test_investment_project_added(api_client):
    """
    Get a list of investment project and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        project = InvestmentProjectFactory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:investment-project-added'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Investment Activities Added',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/investment/project-added'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(project.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInvestmentProject:{project.id}:Add',
                'type': 'Add',
                'published': format_date_or_datetime(project.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'actor': {
                    'id': f'dit:DataHubAdviser:{project.created_by.pk}',
                    'type': ['Person', 'dit:Adviser'],
                    'dit:emailAddress':
                        project.created_by.contact_email or project.created_by.email,
                    'name': project.created_by.name,
                },
                'object': {
                    'id': f'dit:DataHubInvestmentProject:{project.id}',
                    'type': ['dit:InvestmentProject'],
                    'startTime': format_date_or_datetime(project.created_on),
                    'name': project.name,
                    'dit:investmentType': {
                        'name': project.investment_type.name,
                    },
                    'dit:estimatedLandDate': format_date_or_datetime(
                        project.estimated_land_date,
                    ),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{project.investor_company.pk}',
                            'dit:dunsNumber': project.investor_company.duns_number,
                            'dit:companiesHouseNumber': project.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': project.investor_company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
                                'name': contact.name,
                            }
                            for contact in project.client_contacts.order_by('pk')
                        ],
                    ],
                    'url': project.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_investment_project_with_pm_added(api_client):
    """
    Get a list of investment project and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/

    Investment Project with PM will have fields such as totalInvestment and
    numberNewJobs.
    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        project = AssignPMInvestmentProjectFactory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:investment-project-added'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Investment Activities Added',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/investment/project-added'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(project.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInvestmentProject:{project.id}:Add',
                'type': 'Add',
                'published': format_date_or_datetime(project.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'actor': {
                    'id': f'dit:DataHubAdviser:{project.created_by.pk}',
                    'type': ['Person', 'dit:Adviser'],
                    'dit:emailAddress':
                        project.created_by.contact_email or project.created_by.email,
                    'name': project.created_by.name,
                },
                'object': {
                    'id': f'dit:DataHubInvestmentProject:{project.id}',
                    'type': ['dit:InvestmentProject'],
                    'startTime': format_date_or_datetime(project.created_on),
                    'name': project.name,
                    'dit:investmentType': {
                        'name': project.investment_type.name,
                    },
                    'dit:estimatedLandDate': format_date_or_datetime(
                        project.estimated_land_date,
                    ),
                    'dit:totalInvestment': project.total_investment,
                    'dit:numberNewJobs': project.number_new_jobs,
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{project.investor_company.pk}',
                            'dit:dunsNumber': project.investor_company.duns_number,
                            'dit:companiesHouseNumber': project.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': project.investor_company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
                                'name': contact.name,
                            }
                            for contact in project.client_contacts.order_by('pk')
                        ],
                    ],
                    'url': project.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_investment_project_verify_win_added(api_client):
    """
    Get a list of investment project and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/

    Investment Project with verified win will have fields such as totalInvestment,
    numberNewJobs and foreignEquityInvestment.

    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        project = VerifyWinInvestmentProjectFactory()
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:investment-project-added'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Investment Activities Added',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/investment/project-added'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(project.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInvestmentProject:{project.id}:Add',
                'type': 'Add',
                'published': format_date_or_datetime(project.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'actor': {
                    'id': f'dit:DataHubAdviser:{project.created_by.pk}',
                    'type': ['Person', 'dit:Adviser'],
                    'dit:emailAddress':
                        project.created_by.contact_email or project.created_by.email,
                    'name': project.created_by.name,
                },
                'object': {
                    'id': f'dit:DataHubInvestmentProject:{project.id}',
                    'type': ['dit:InvestmentProject'],
                    'startTime': format_date_or_datetime(project.created_on),
                    'name': project.name,
                    'dit:investmentType': {
                        'name': project.investment_type.name,
                    },
                    'dit:estimatedLandDate': format_date_or_datetime(
                        project.estimated_land_date,
                    ),
                    'dit:totalInvestment': project.total_investment,
                    'dit:foreignEquityInvestment': project.foreign_equity_investment,
                    'dit:numberNewJobs': project.number_new_jobs,
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{project.investor_company.pk}',
                            'dit:dunsNumber': project.investor_company.duns_number,
                            'dit:companiesHouseNumber': project.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': project.investor_company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
                                'name': contact.name,
                            }
                            for contact in project.client_contacts.order_by('pk')
                        ],
                    ],
                    'url': project.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_investment_project_added_with_gva(api_client):
    """
    This test adds the necessary fields to compute gross_value_added property
    and tests if its included in the response.
    """
    start = datetime.datetime(year=2012, month=7, day=12, hour=15, minute=6, second=3)
    with freeze_time(start) as frozen_datetime:
        project = InvestmentProjectFactory(
            foreign_equity_investment=10000,
            sector_id=constants.Sector.aerospace_assembly_aircraft.value.id,
            investment_type_id=constants.InvestmentType.fdi.value.id,
        )
        frozen_datetime.tick(datetime.timedelta(seconds=1, microseconds=1))
        response = hawk.get(api_client, get_url('api-v3:activity-stream:investment-project-added'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Investment Activities Added',
        'type': 'OrderedCollectionPage',
        'next': 'http://testserver/v3/activity-stream/investment/project-added'
                + '?cursor=2012-07-12T15%3A06%3A03.000000%2B00%3A00'
                + f'&cursor={str(project.id)}',
        'orderedItems': [
            {
                'id': f'dit:DataHubInvestmentProject:{project.id}:Add',
                'type': 'Add',
                'published': format_date_or_datetime(project.created_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'actor': {
                    'id': f'dit:DataHubAdviser:{project.created_by.pk}',
                    'type': ['Person', 'dit:Adviser'],
                    'dit:emailAddress':
                        project.created_by.contact_email or project.created_by.email,
                    'name': project.created_by.name,
                },
                'object': {
                    'id': f'dit:DataHubInvestmentProject:{project.id}',
                    'type': ['dit:InvestmentProject'],
                    'startTime': format_date_or_datetime(project.created_on),
                    'name': project.name,
                    'dit:investmentType': {
                        'name': project.investment_type.name,
                    },
                    'dit:estimatedLandDate': format_date_or_datetime(
                        project.estimated_land_date,
                    ),
                    'dit:foreignEquityInvestment': 10000.0,
                    'dit:grossValueAdded': 519835140.0,
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{project.investor_company.pk}',
                            'dit:dunsNumber': project.investor_company.duns_number,
                            'dit:companiesHouseNumber': project.investor_company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': project.investor_company.name,
                        },
                        *[
                            {
                                'id': f'dit:DataHubContact:{contact.pk}',
                                'type': ['Person', 'dit:Contact'],
                                'url': contact.get_absolute_url(),
                                'dit:emailAddress': contact.email,
                                'dit:jobTitle': contact.job_title,
                                'name': contact.name,
                            }
                            for contact in project.client_contacts.order_by('pk')
                        ],
                    ],
                    'url': project.get_absolute_url(),
                },
            },
        ],
    }
