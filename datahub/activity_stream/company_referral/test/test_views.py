import pytest
from freezegun import freeze_time
from rest_framework import status

from datahub.activity_stream.test import hawk
from datahub.activity_stream.test.utils import get_url
from datahub.company.test.factories import AdviserFactory
from datahub.company_referral.test.factories import (
    ClosedCompanyReferralFactory,
    CompanyReferralFactory,
    CompleteCompanyReferralFactory,
)
from datahub.core.test_utils import format_date_or_datetime


@pytest.mark.django_db
def test_company_referral_activity(api_client):
    """
    Get a list of company referrals and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    company_referral = CompanyReferralFactory()
    response = hawk.get(api_client, get_url('api-v3:activity-stream:company-referrals'))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Company Referral Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/company-referral',
        'partOf': 'http://testserver/v3/activity-stream/company-referral',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubCompanyReferral:{company_referral.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(company_referral.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubCompanyReferral:{company_referral.id}',
                    'startTime': format_date_or_datetime(company_referral.created_on),
                    'dit:subject': company_referral.subject,
                    'dit:status': str(company_referral.status),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{company_referral.company.pk}',
                            'dit:dunsNumber': company_referral.company.duns_number,
                            'dit:companiesHouseNumber': company_referral.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': company_referral.company.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.created_by.contact_email
                                or company_referral.created_by.email,
                            'name': company_referral.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.created_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'sender',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.recipient.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.recipient.contact_email
                                or company_referral.recipient.email,
                            'name': company_referral.recipient.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.recipient.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.recipient.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'recipient',
                        },
                        {
                            'id': f'dit:DataHubContact:{company_referral.contact.pk}',
                            'type': ['Person', 'dit:Contact'],
                            'url': company_referral.contact.get_absolute_url(),
                            'dit:emailAddress': company_referral.contact.email,
                            'dit:jobTitle': company_referral.contact.job_title,
                            'name': company_referral.contact.name,
                        },
                    ],
                    'url': company_referral.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_closed_company_referral_activity(api_client):
    """
    Get a list of closed company referrals and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    company_referral = ClosedCompanyReferralFactory()
    response = hawk.get(api_client, get_url('api-v3:activity-stream:company-referrals'))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Company Referral Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/company-referral',
        'partOf': 'http://testserver/v3/activity-stream/company-referral',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubCompanyReferral:{company_referral.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(company_referral.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubCompanyReferral:{company_referral.id}',
                    'startTime': format_date_or_datetime(company_referral.created_on),
                    'dit:subject': company_referral.subject,
                    'dit:status': str(company_referral.status),
                    'dit:closedOn': format_date_or_datetime(company_referral.closed_on),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{company_referral.company.pk}',
                            'dit:dunsNumber': company_referral.company.duns_number,
                            'dit:companiesHouseNumber': company_referral.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': company_referral.company.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.created_by.contact_email
                                or company_referral.created_by.email,
                            'name': company_referral.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.created_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'sender',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.recipient.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.recipient.contact_email
                                or company_referral.recipient.email,
                            'name': company_referral.recipient.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.recipient.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.recipient.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'recipient',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.closed_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.closed_by.contact_email
                                or company_referral.closed_by.email,
                            'name': company_referral.closed_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.closed_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.closed_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'closer',
                        },
                        {
                            'id': f'dit:DataHubContact:{company_referral.contact.pk}',
                            'type': ['Person', 'dit:Contact'],
                            'url': company_referral.contact.get_absolute_url(),
                            'dit:emailAddress': company_referral.contact.email,
                            'dit:jobTitle': company_referral.contact.job_title,
                            'name': company_referral.contact.name,
                        },
                    ],
                    'url': company_referral.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_complete_company_referral_activity(api_client):
    """
    Get a list of completed company referrals and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    company_referral = CompleteCompanyReferralFactory()
    response = hawk.get(api_client, get_url('api-v3:activity-stream:company-referrals'))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Company Referral Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/company-referral',
        'partOf': 'http://testserver/v3/activity-stream/company-referral',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubCompanyReferral:{company_referral.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(company_referral.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubCompanyReferral:{company_referral.id}',
                    'startTime': format_date_or_datetime(company_referral.created_on),
                    'dit:subject': company_referral.subject,
                    'dit:status': str(company_referral.status),
                    'dit:completedOn': format_date_or_datetime(company_referral.completed_on),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{company_referral.company.pk}',
                            'dit:dunsNumber': company_referral.company.duns_number,
                            'dit:companiesHouseNumber': company_referral.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': company_referral.company.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.created_by.contact_email
                                or company_referral.created_by.email,
                            'name': company_referral.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.created_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'sender',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.recipient.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.recipient.contact_email
                                or company_referral.recipient.email,
                            'name': company_referral.recipient.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.recipient.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.recipient.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'recipient',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.completed_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.completed_by.contact_email
                                or company_referral.completed_by.email,
                            'name': company_referral.completed_by.name,
                            'dit:team': {
                                'id':
                                    f'dit:DataHubTeam:{company_referral.completed_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.completed_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'completer',
                        },
                        {
                            'id': f'dit:DataHubContact:{company_referral.contact.pk}',
                            'type': ['Person', 'dit:Contact'],
                            'url': company_referral.contact.get_absolute_url(),
                            'dit:emailAddress': company_referral.contact.email,
                            'dit:jobTitle': company_referral.contact.job_title,
                            'name': company_referral.contact.name,
                        },
                    ],
                    'url': company_referral.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_company_referral_activity_without_team_and_contact(api_client):
    """
    Get a list of company referrals and test the returned JSON is valid as per:
    https://www.w3.org/TR/activitystreams-core/
    """
    recipient = AdviserFactory(dit_team=None)
    company_referral = CompanyReferralFactory(recipient=recipient, contact=None)
    response = hawk.get(api_client, get_url('api-v3:activity-stream:company-referrals'))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'summary': 'Company Referral Activities',
        'type': 'OrderedCollectionPage',
        'id': 'http://testserver/v3/activity-stream/company-referral',
        'partOf': 'http://testserver/v3/activity-stream/company-referral',
        'previous': None,
        'next': None,
        'orderedItems': [
            {
                'id': f'dit:DataHubCompanyReferral:{company_referral.id}:Announce',
                'type': 'Announce',
                'published': format_date_or_datetime(company_referral.modified_on),
                'generator': {'name': 'dit:dataHub', 'type': 'Application'},
                'object': {
                    'id': f'dit:DataHubCompanyReferral:{company_referral.id}',
                    'startTime': format_date_or_datetime(company_referral.created_on),
                    'dit:subject': company_referral.subject,
                    'dit:status': str(company_referral.status),
                    'attributedTo': [
                        {
                            'id': f'dit:DataHubCompany:{company_referral.company.pk}',
                            'dit:dunsNumber': company_referral.company.duns_number,
                            'dit:companiesHouseNumber': company_referral.company.company_number,
                            'type': ['Organization', 'dit:Company'],
                            'name': company_referral.company.name,
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.created_by.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.created_by.contact_email
                                or company_referral.created_by.email,
                            'name': company_referral.created_by.name,
                            'dit:team': {
                                'id': f'dit:DataHubTeam:{company_referral.created_by.dit_team.pk}',
                                'type': ['Group', 'dit:Team'],
                                'name': company_referral.created_by.dit_team.name,
                            },
                            'dit:DataHubCompanyReferral:role': 'sender',
                        },
                        {
                            'id': f'dit:DataHubAdviser:{company_referral.recipient.pk}',
                            'type': ['Person', 'dit:Adviser'],
                            'dit:emailAddress':
                                company_referral.recipient.contact_email
                                or company_referral.recipient.email,
                            'name': company_referral.recipient.name,
                            'dit:DataHubCompanyReferral:role': 'recipient',
                        },
                    ],
                    'url': company_referral.get_absolute_url(),
                },
            },
        ],
    }


@pytest.mark.django_db
def test_company_referrals_ordering(api_client):
    """
    Test that the company referrals are ordered by ('modified_on', 'pk')
    """
    company_referrals = []

    # We create 2 interactions with the same modified_on time
    with freeze_time():
        company_referrals += CompanyReferralFactory.create_batch(2)
    company_referrals += CompanyReferralFactory.create_batch(8)
    response = hawk.get(api_client, get_url('api-v3:activity-stream:company-referrals'))
    assert response.status_code == status.HTTP_200_OK

    sorted_company_referral_ids = [
        f'dit:DataHubCompanyReferral:{obj.pk}'
        for obj in sorted(company_referrals, key=lambda obj: (obj.modified_on, obj.pk))
    ]
    response_company_referral_ids = [
        item['object']['id']
        for item in response.json()['orderedItems']
    ]
    assert sorted_company_referral_ids == response_company_referral_ids
