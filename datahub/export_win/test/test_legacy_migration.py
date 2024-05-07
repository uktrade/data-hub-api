from datetime import datetime, timezone

import pytest

from dateutil import parser

from django.conf import settings
from freezegun import freeze_time

from rest_framework import status

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.core.test_utils import HawkMockJSONResponse
from datahub.export_win.legacy_migration import (
    migrate_all_legacy_wins,
)
from datahub.export_win.models import (
    Win,
)
from datahub.export_win.test.factories import (
    LegacyExportWinsToDataHubCompanyFactory,
)

pytestmark = pytest.mark.django_db


mock_legacy_wins_page_urls = {
    'wins': [
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-wins',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-wins?cursor=1&source=L',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-wins?cursor=2&source=E',
    ],
    'breakdowns': [
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-breakdowns',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-breakdowns?cursor=1&source=L',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-breakdowns?cursor=2&source=E',
    ],
    'advisers': [
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisers',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisers?cursor=1&source=L',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisers?cursor=2&source=E',
    ],
}

legacy_wins = {
    mock_legacy_wins_page_urls['wins'][0]: {
        'next': mock_legacy_wins_page_urls['wins'][1],
        'results': [{
            'associated_programme_1': 1,
            'associated_programme_2': 2,
            'associated_programme_3': 3,
            'associated_programme_4': 9,
            'associated_programme_5': 11,
            'audit': None,
            'business_potential': None,
            'business_type': '4',
            'cdms_reference': 'abcd',
            'company_name': 'Lambda',
            'complete': True,
            'confirmation__access_to_contacts': 5,
            'confirmation__access_to_information': 5,
            'confirmation__agree_with_win': None,
            'confirmation__case_study_willing': False,
            'confirmation__comments': '',
            'confirmation__company_was_at_risk_of_not_exporting': True,
            'confirmation__created': '2024-01-23T01:12:47.221146Z',
            'confirmation__developed_relationships': 1,
            'confirmation__gained_confidence': 3,
            'confirmation__has_enabled_expansion_into_existing_market': False,
            'confirmation__has_enabled_expansion_into_new_market': True,
            'confirmation__has_explicit_export_plans': False,
            'confirmation__has_increased_exports_as_percent_of_turnover': True,
            'confirmation__improved_profile': 3,
            'confirmation__interventions_were_prerequisite': False,
            'confirmation__involved_state_enterprise': False,
            'confirmation__name': 'John M Doe',
            'confirmation__other_marketing_source': 'Web',
            'confirmation__our_support': 0,
            'confirmation__overcame_problem': 0,
            'confirmation__support_improved_speed': True,
            'country': 'AT',
            'created': '2024-01-22T01:12:47.221126Z',
            'customer_email_address': 'test@test.email',
            'customer_job_title': 'Director',
            'customer_location': 1,
            'customer_name': 'John M Doe',
            'date': '2024-02-01',
            'description': 'Lorem ipsum',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'hq_team': 'itt:DIT Team East Midlands - International Trade Team',
            'hvc': None,
            'hvo_programme': '',
            'id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
            'is_e_exported': False,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': False,
            'lead_officer_email_address': '',
            'lead_officer_name': 'Jane Doe',
            'line_manager_name': 'Linem Anager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'team_type': 'itt',
            'type_of_support_1': 1,
            'type_of_support_2': 2,
            'type_of_support_3': None,
            'user__email': 'user.email@trade.gov.uk',
            'user__name': 'User Email',
            'sector_display': 'Creative industries : Art',
            'confirmation_last_export':
                'Apart from this win, we have exported in the last 12 months',
            'confirmation_marketing_source': 'Don’t know',
            'confirmation_portion_without_help': 'No value without our help',
            'country_name': 'Austria',
        }],
    },
    mock_legacy_wins_page_urls['wins'][1]: {
        'next': mock_legacy_wins_page_urls['wins'][2],
        'results': [{
            'associated_programme_1': 1,
            'associated_programme_2': 2,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '3',
            'cdms_reference': 'abcd',
            'company_name': 'Lambda',
            'complete': True,
            'confirmation__access_to_contacts': 5,
            'confirmation__access_to_information': 5,
            'confirmation__agree_with_win': None,
            'confirmation__case_study_willing': False,
            'confirmation__comments': '',
            'confirmation__company_was_at_risk_of_not_exporting': True,
            'confirmation__created': '2024-02-25T01:12:48.111131Z',
            'confirmation__developed_relationships': 1,
            'confirmation__gained_confidence': 3,
            'confirmation__has_enabled_expansion_into_existing_market': False,
            'confirmation__has_enabled_expansion_into_new_market': True,
            'confirmation__has_explicit_export_plans': False,
            'confirmation__has_increased_exports_as_percent_of_turnover': True,
            'confirmation__improved_profile': 3,
            'confirmation__interventions_were_prerequisite': False,
            'confirmation__involved_state_enterprise': False,
            'confirmation__name': 'John Doe',
            'confirmation__other_marketing_source': 'Web',
            'confirmation__our_support': 0,
            'confirmation__overcame_problem': 0,
            'confirmation__support_improved_speed': True,
            'country': 'US',
            'created': '2024-02-24T01:12:47.221126Z',
            'customer_email_address': 'test@test.email',
            'customer_job_title': 'Director',
            'customer_location': 1,
            'customer_name': 'John Doe',
            'date': '2024-04-01',
            'description': 'Lorem ipsum',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'hq_team': 'itt:DIT Team East Midlands - International Trade Team',
            'hvc': None,
            'hvo_programme': '',
            'id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
            'is_e_exported': False,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': False,
            'lead_officer_email_address': '',
            'lead_officer_name': 'Jane Smith',
            'line_manager_name': 'Linem Anager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'team_type': 'itt',
            'type_of_support_1': 1,
            'type_of_support_2': 2,
            'type_of_support_3': None,
            'user__email': 'user.email1@trade.gov.uk',
            'user__name': 'User Email',
            'sector_display': 'Creative industries : Art',
            'confirmation_last_export':
                'Apart from this win, we have exported in the last 12 months',
            'confirmation_marketing_source': 'Don’t know',
            'confirmation_portion_without_help': 'No value without our help',
            'country_name': 'Austria',
        }],
    },
    mock_legacy_wins_page_urls['breakdowns'][0]: {
        'next': mock_legacy_wins_page_urls['breakdowns'][1],
        'results': [
            {
                'id': 5,
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
                'type': 1,
                'year': 2023,
                'value': 3000,
            },
            {
                'id': 6,
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
                'type': 1,
                'year': 2024,
                'value': 4000,
            },
            {
                'id': 7,
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
                'type': 1,
                'year': 2025,
                'value': 5000,
            },
            {
                'id': 8,
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
                'type': 1,
                'year': 2026,
                'value': 6000,
            },
            {
                'id': 9,
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
                'type': 1,
                'year': 2027,
                'value': 3000,
            },
        ],
    },
    mock_legacy_wins_page_urls['breakdowns'][1]: {
        'next': mock_legacy_wins_page_urls['breakdowns'][2],
        'results': [
            {
                'id': 10,
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
                'type': 1,
                'year': 2024,
                'value': 3000,
            },
            {
                'id': 11,
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
                'type': 1,
                'year': 2025,
                'value': 4000,
            },
            {
                'id': 12,
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
                'type': 1,
                'year': 2026,
                'value': 5000,
            },
            {
                'id': 13,
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
                'type': 1,
                'year': 2027,
                'value': 6000,
            },
            {
                'id': 14,
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
                'type': 1,
                'year': 2028,
                'value': 3000,
            },
        ],
    },
    mock_legacy_wins_page_urls['advisers'][0]: {
        'next': mock_legacy_wins_page_urls['advisers'][1],
        'results': [
            {
                'hq_team': 'itt:The North West International Trade Team',
                'id': 1,
                'location': 'Manchester',
                'name': 'John Doe',
                'team_type': 'itt',
                'win__id': '4c90a214-035f-4445-b6a1-ca7af3486f8c',
            },
        ],
    },
    mock_legacy_wins_page_urls['advisers'][1]: {
        'next': mock_legacy_wins_page_urls['advisers'][2],
        'results': [
            {
                'hq_team': 'itt:The North West International Trade Team',
                'id': 1,
                'location': 'London',
                'name': 'John Smith',
                'team_type': 'itt',
                'win__id': '02ce5d82-5294-477a-ab9a-94782e7b2794',
            },
        ],
    },
}


@pytest.fixture
def mock_legacy_wins_pages(requests_mock):
    for url, data in legacy_wins.items():
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response=data,
        )
        requests_mock.get(
            url.replace(settings.EXPORT_WINS_SERVICE_BASE_URL, ''),
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )


def test_legacy_migration(mock_legacy_wins_pages):
    """Tests that legacy wins are migrated."""
    company = CompanyFactory()
    LegacyExportWinsToDataHubCompanyFactory(
        id='4c90a214-035f-4445-b6a1-ca7af3486f8c',
        company=company,
    )
    jane_doe = AdviserFactory(
        first_name='Jane',
        last_name='Doe',
    )
    john_smith = AdviserFactory(
        first_name='John',
        last_name='Smith',
    )
    adviser = AdviserFactory(
        contact_email='user.email@trade.gov.uk',
    )
    contact = ContactFactory(
        company=company,
        first_name='John',
        last_name='Doe',
    )

    current_date = datetime.now(tz=timezone.utc)

    with freeze_time(current_date):
        migrate_all_legacy_wins()

    win_1 = Win.objects.get(id='4c90a214-035f-4445-b6a1-ca7af3486f8c')
    assert win_1.company_contacts.first() == contact
    assert win_1.company == company
    assert win_1.lead_officer == jane_doe
    assert win_1.adviser == adviser
    assert win_1.total_expected_export_value == 21000
    assert win_1.total_expected_non_export_value == 0
    assert win_1.total_expected_odi_value == 0
    assert win_1.breakdowns.count() == 5
    assert win_1.migrated_on == current_date
    win_1_created_on = parser.parse('2024-01-22T01:12:47.221126Z').astimezone(timezone.utc)
    assert win_1.created_on == win_1_created_on
    assert win_1.customer_response.created_on == win_1_created_on
    win_1_responded_on = parser.parse('2024-01-23T01:12:47.221146Z').astimezone(timezone.utc)
    assert win_1.customer_response.responded_on == win_1_responded_on

    win_1_adviser = win_1.advisers.first()
    assert win_1_adviser.adviser is None
    assert win_1_adviser.name == 'John Doe'

    win_2 = Win.objects.get(id='02ce5d82-5294-477a-ab9a-94782e7b2794')
    assert win_2.company_contacts.count() == 0
    assert win_2.company is None
    assert win_2.company_name == 'Lambda'
    assert win_2.customer_name == 'John Doe'
    assert win_2.lead_officer is None
    assert win_2.lead_officer_name == 'Jane Smith'
    assert win_2.adviser_email_address == 'user.email1@trade.gov.uk'
    assert win_2.adviser is None
    assert win_2.total_expected_export_value == 21000
    assert win_2.total_expected_non_export_value == 0
    assert win_2.total_expected_odi_value == 0
    assert win_2.breakdowns.count() == 5
    assert win_2.advisers.first().adviser == john_smith
    assert win_2.migrated_on == current_date
    win_2_created_on = parser.parse('2024-02-24T01:12:47.221126Z').astimezone(timezone.utc)
    assert win_2.created_on == win_2_created_on
    assert win_2.customer_response.created_on == win_2_created_on
    win_2_responded_on = parser.parse('2024-02-25T01:12:48.111131Z').astimezone(timezone.utc)
    assert win_2.customer_response.responded_on == win_2_responded_on
