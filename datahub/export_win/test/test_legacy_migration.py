from datetime import datetime, timedelta, timezone

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
    _email_mapping,
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
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisors',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisors?cursor=1&source=L',
        f'{settings.EXPORT_WINS_SERVICE_BASE_URL}/datasets/data-hub-advisors?cursor=2&source=E',
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
            'confirmation__created': None,
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
        }, {
            'associated_programme_1': None,
            'associated_programme_2': None,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '8',
            'cdms_reference': 'cdms reference',
            'company_name': 'company name',
            'complete': False,
            'country': 'AL',
            'country_name': 'Albania',
            'created': '2016-06-24T11:32:42.134323Z',
            'customer_email_address': 'test@test.com',
            'customer_job_title': 'customer job title',
            'customer_location': 3,
            'customer_name': 'customer name',
            'date': '2016-01-01',
            'description': 'asdf',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'hq_team': 'team:1',
            'hvc': None,
            'hvo_programme': 'AER-01',
            'id': '1239d123-1123-4123-80d1-997054dd03f7',
            'is_e_exported': True,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': True,
            'lead_officer_email_address': '',
            'lead_officer_name': 'Lead officer name',
            'line_manager_name': 'line manager name',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'sector_display': 'Advanced engineering',
            'team_type': 'team',
            'type_of_support_1': 1,
            'type_of_support_2': None,
            'type_of_support_3': None,
            'user__email': 'abc@test',
            'user__name': 'Abc Def',
        }, {
            'associated_programme_1': None,
            'associated_programme_2': None,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '8',
            'cdms_reference': 'cdms reference',
            'company_name': 'company name',
            'complete': False,
            'country': 'AL',
            'country_name': 'Albania',
            'created': '2016-06-24T11:32:42.134323Z',
            'customer_email_address': 'test@test.com',
            'customer_job_title': 'customer job title',
            'customer_location': 3,
            'customer_name': 'customer name',
            'date': '2016-01-01',
            'description': 'asdf',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'confirmation__comments': None,
            'hq_team': 'team:1',
            'hvc': None,
            'hvo_programme': 'AER-01',
            'id': '03458ea2-2804-4f9c-b9e0-389ca8fadf90',
            'is_e_exported': True,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': True,
            'lead_officer_email_address': '',
            'lead_officer_name': 'Lead officer name',
            'line_manager_name': 'line manager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'sector_display': None,
            'team_type': 'team',
            'type_of_support_1': 1,
            'type_of_support_2': None,
            'type_of_support_3': None,
            'user__email': 'abc@test',
            'user__name': 'Abc Def',
            'confirmation__comments': None,
            'confirmation__name': None,
            'confirmation__other_marketing_source': None,
        }, {
            'associated_programme_1': None,
            'associated_programme_2': None,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '8',
            'cdms_reference': 'cdms reference',
            'company_name': 'company name',
            'complete': False,
            'country': 'AL',
            'country_name': 'abc',
            'created': '2016-06-24T11:32:42.134323Z',
            'customer_email_address': 'test@test.com',
            'customer_job_title': 'customer job title',
            'customer_location': 3,
            'customer_name': 'customer name',
            'date': '2016-01-01',
            'description': 'asdf',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'confirmation__comments': None,
            'hq_team': 'team:1',
            'hvc': None,
            'hvo_programme': 'AER-01',
            'id': 'c84caade-4fae-4af0-816f-e27a8c5ded95',
            'is_e_exported': True,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': True,
            'lead_officer_email_address': '',
            'lead_officer_name': 'Lead officer name',
            'line_manager_name': 'line manager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'sector_display': None,
            'team_type': 'team',
            'type_of_support_1': 1,
            'type_of_support_2': None,
            'type_of_support_3': None,
            'user__email': 'abc@test',
            'user__name': 'Abc Def',
            'confirmation__comments': None,
            'confirmation__name': None,
            'confirmation__other_marketing_source': None,
        }, {
            'associated_programme_1': None,
            'associated_programme_2': None,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '8',
            'cdms_reference': 'cdms reference',
            'company_name': 'company name',
            'complete': False,
            'country': 'AL',
            'country_name': 'Albania',
            'created': '2016-06-24T11:32:42.134323Z',
            'customer_email_address': 'test@test.com',
            'customer_job_title': 'customer job title',
            'customer_location': 3,
            'customer_name': 'customer name',
            'date': '2016-01-01',
            'description': 'asdf',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'confirmation__comments': None,
            'hq_team': '',
            'hvc': None,
            'hvo_programme': 'AER-01',
            'id': '5778b485-1060-46e2-b411-772cd0f76d79',
            'is_e_exported': True,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': True,
            'lead_officer_email_address': 'user.email2@trade.gov.uk',
            'lead_officer_name': 'Lead officer name',
            'line_manager_name': 'line manager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'sector_display': None,
            'team_type': 'team',
            'type_of_support_1': 1,
            'type_of_support_2': None,
            'type_of_support_3': None,
            'user__email': 'abc@test',
            'user__name': 'Abc Def',
            'confirmation__comments': None,
            'confirmation__name': None,
            'confirmation__other_marketing_source': None,
            'is_active': False,
        }, {  # Tests if deleted win will be updated
            'associated_programme_1': None,
            'associated_programme_2': None,
            'associated_programme_3': None,
            'associated_programme_4': None,
            'associated_programme_5': None,
            'audit': None,
            'business_potential': None,
            'business_type': '8',
            'cdms_reference': 'cdms reference',
            'company_name': 'company name',
            'complete': False,
            'country': 'AL',
            'country_name': 'Albania',
            'created': '2016-06-24T11:32:42.134323Z',
            'customer_email_address': 'test@test.com',
            'customer_job_title': 'customer job title',
            'customer_location': 3,
            'customer_name': 'customer name',
            'date': '2016-01-01',
            'description': 'asdf',
            'export_experience': None,
            'goods_vs_services': 1,
            'has_hvo_specialist_involvement': False,
            'confirmation__comments': None,
            'hq_team': 'team:1',
            'hvc': None,
            'hvo_programme': 'AER-01',
            'id': '5778b485-1060-46e2-b411-772cd0f76d79',
            'is_e_exported': True,
            'is_line_manager_confirmed': True,
            'is_personally_confirmed': True,
            'is_prosperity_fund_related': True,
            'lead_officer_email_address': 'user.email2@trade.gov.uk',
            'lead_officer_name': 'Lead officer name',
            'line_manager_name': 'line manager',
            'name_of_customer': '',
            'name_of_export': '',
            'other_official_email_address': '',
            'sector_display': None,
            'team_type': 'team',
            'type_of_support_1': 1,
            'type_of_support_2': None,
            'type_of_support_3': None,
            'user__email': 'abc@test',
            'user__name': 'Abc Def',
            'confirmation__comments': None,
            'confirmation__name': None,
            'confirmation__other_marketing_source': None,
            'is_active': False,
        }],
    },
    mock_legacy_wins_page_urls['breakdowns'][0]: {
        'next': mock_legacy_wins_page_urls['breakdowns'][1],
        'results': [
            {
                'id': 11,
                'win__id': '5778b485-1060-46e2-b411-772cd0f76d79',
                'type': 1,
                'year': 2016,
                'value': 3000,
                'is_active': False,
            },
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
            {  # For orphaned breakdown
                'id': 24,
                'win__id': '28065639-a538-4f0c-9fe7-bb39c39668c0',
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
        is_active=True,
    )
    john_smith = AdviserFactory(
        first_name='John',
        last_name='Smith',
        is_active=True,
    )
    AdviserFactory(
        first_name='John',
        last_name='Smith',
        is_active=False,
    )
    line_manager = AdviserFactory(
        first_name='line',
        last_name='manager',
    )
    adviser = AdviserFactory(
        contact_email='user.email@businessandtrade.gov.uk',
        is_active=True,
    )
    adviser2 = AdviserFactory(
        email='user.email2@trade.gov.uk',
        is_active=False,
    )
    current_date = datetime.utcnow()
    with freeze_time(current_date):
        contact = ContactFactory(
            company=company,
            first_name='John',
            last_name='Doe',
        )
    with freeze_time(current_date - timedelta(days=1)):
        ContactFactory(
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
    assert win_2.customer_response.responded_on is None

    win_3 = Win.objects.get(id='1239d123-1123-4123-80d1-997054dd03f7')
    assert win_3.company_contacts.count() == 0
    assert win_3.company is None
    assert win_3.company_name == 'company name'
    assert win_3.customer_name == 'customer name'
    assert win_3.lead_officer is None
    assert win_3.lead_officer_name == 'Lead officer name'
    assert win_3.adviser_email_address == 'abc@test'
    assert win_3.adviser is None
    assert win_3.total_expected_export_value == 0
    assert win_3.total_expected_non_export_value == 0
    assert win_3.total_expected_odi_value == 0
    assert win_3.breakdowns.count() == 0
    assert win_3.advisers.count() == 0
    assert win_3.migrated_on == current_date
    win_3_created_on = parser.parse('2016-06-24T11:32:42.134323Z').astimezone(timezone.utc)
    assert win_3.created_on == win_3_created_on
    assert win_3.customer_response.created_on == win_3_created_on
    assert win_3.customer_response.responded_on is None

    win_4 = Win.objects.get(id='03458ea2-2804-4f9c-b9e0-389ca8fadf90')
    assert win_4.company_contacts.count() == 0
    assert win_4.company is None
    assert win_4.company_name == 'company name'
    assert win_4.customer_name == 'customer name'
    assert win_4.lead_officer is None
    assert win_4.lead_officer_name == 'Lead officer name'
    assert win_4.adviser_email_address == 'abc@test'
    assert win_4.adviser is None
    assert win_4.total_expected_export_value == 0
    assert win_4.total_expected_non_export_value == 0
    assert win_4.total_expected_odi_value == 0
    assert win_4.breakdowns.count() == 0
    assert win_4.advisers.count() == 0
    assert win_4.migrated_on == current_date
    win_4_created_on = parser.parse('2016-06-24T11:32:42.134323Z').astimezone(timezone.utc)
    assert win_4.created_on == win_4_created_on
    assert win_4.customer_response.created_on == win_4_created_on
    assert win_4.customer_response.responded_on is None
    assert win_4.sector_id is None
    assert win_4.customer_response.name == ''
    assert win_4.customer_response.comments == ''
    assert win_4.customer_response.other_marketing_source == ''
    assert win_4.line_manager == line_manager

    assert Win.objects.filter(id='c84caade-4fae-4af0-816f-e27a8c5ded95').exists() is False

    win_6 = Win.objects.all_wins().get(id='5778b485-1060-46e2-b411-772cd0f76d79')
    assert win_6.company_contacts.count() == 0
    assert win_6.company is None
    assert win_6.company_name == 'company name'
    assert win_6.customer_name == 'customer name'
    assert win_6.lead_officer == adviser2
    assert win_6.lead_officer_name == ''
    assert win_6.adviser_email_address == 'abc@test'
    assert win_6.adviser is None
    assert win_6.total_expected_export_value == 3000
    assert win_6.total_expected_non_export_value == 0
    assert win_6.total_expected_odi_value == 0
    assert win_6.breakdowns.count() == 1
    assert win_6.advisers.count() == 0
    assert win_6.migrated_on == current_date
    win_6_created_on = parser.parse('2016-06-24T11:32:42.134323Z').astimezone(timezone.utc)
    assert win_6.created_on == win_6_created_on
    assert win_6.customer_response.created_on == win_6_created_on
    assert win_6.customer_response.responded_on is None
    assert win_6.sector_id is None
    assert win_6.customer_response.name == ''
    assert win_6.customer_response.comments == ''
    assert win_6.customer_response.other_marketing_source == ''
    assert win_6.line_manager == line_manager
    assert win_6.is_deleted is True


@pytest.mark.parametrize(
    'email,expected',
    (
        ('test@trade.gov.uk', {'test@businessandtrade.gov.uk', 'test@trade.gov.uk'}),
        ('test@mobile.trade.gov.uk', {
            'test@mobile.trade.gov.uk',
            'test@mobile.ukti.gov.uk',
            'test@businessandtrade.gov.uk',
        }),
        ('test@ukti', {'test@trade', 'test@ukti'}),
    ),
)
def test_email_mapping(email, expected):
    result = _email_mapping(email)
    assert result == expected
