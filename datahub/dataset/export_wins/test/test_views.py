from datetime import date, datetime, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from factory import Iterator
from freezegun import freeze_time

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import Sector
from datahub.core.test_utils import (
    format_date_or_datetime,
)
from datahub.core.utils import get_financial_year
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.dataset.export_wins import (
    EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
)
from datahub.export_win.constants import EXPORT_WINS_LEGACY_ID_START_VALUE
from datahub.export_win.models import HVC, Win
from datahub.export_win.test.factories import (
    AssociatedProgrammeFactory,
    BreakdownFactory,
    CustomerResponseFactory,
    CustomerResponseTokenFactory,
    HVCFactory,
    HVOProgrammesFactory,
    SupportTypeFactory,
    WinAdviserFactory,
    WinFactory,
)
from datahub.feature_flag.test.factories import (
    FeatureFlagFactory,
)

pytestmark = pytest.mark.django_db


def get_export_wins_legacy_data_feature_flag():
    """Creates the Export wins legacy dataset feature flag.
    """
    return FeatureFlagFactory(
        code=EXPORT_WINS_LEGACY_DATASET_FEATURE_FLAG_NAME,
        is_active=True,
    )


class TestExportWinsAdvisersDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-advisers-dataset')
    factory = WinAdviserFactory

    def _assert_win_adviser_matches_result(self, win_adviser, result):
        assert result == {
            'created_on': format_date_or_datetime(win_adviser.created_on),
            'id': win_adviser.legacy_id,
            'location': win_adviser.location,
            'name': win_adviser.adviser.name if win_adviser.adviser else win_adviser.name,
            'win__id': str(win_adviser.win.id),
            'hq_team_display': win_adviser.hq_team.name,
            'team_type_display': win_adviser.team_type.name,
            'hq_team': win_adviser.hq_team.export_win_id,
            'team_type': win_adviser.team_type.export_win_id,
        }

    def test_success(self, data_flow_api_client):

        win_adviser = self.factory(location='Somewhere')

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_adviser_matches_result(win_adviser, response['results'][0])

    @pytest.mark.parametrize(
        'list_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_data(
        self,
        list_legacy_data,
        data_flow_api_client,
    ):
        if list_legacy_data:
            assert get_export_wins_legacy_data_feature_flag()

        self.factory()
        params = {
            'win': WinFactory(migrated_on=datetime.now()),
        }
        self.factory(**params)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == (2 if list_legacy_data else 1)

    @pytest.mark.parametrize(
        'allow_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_content_override(
        self,
        allow_legacy_data,
        data_flow_api_client,
    ):
        win_advisers = [self.factory()]
        params = {
            'win': WinFactory(migrated_on=datetime.now()),
            'adviser': None,
            'name': 'John Doe',
        }
        win_advisers.append(self.factory(**params))

        response = data_flow_api_client.get(
            self.view_url,
            {
                'legacy_data': allow_legacy_data,
            },
        ).json()

        assert len(response['results']) == (2 if allow_legacy_data else 1)
        for i, result in enumerate(response['results']):
            self._assert_win_adviser_matches_result(win_advisers[i], result)

    def test_with_multiple_win_adviser(self, data_flow_api_client):
        win_advisers = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_win_adviser_matches_result(win_advisers[i], result)

    def test_with_win_id(self, data_flow_api_client):
        win_advisers = self.factory.create_batch(3)

        response = data_flow_api_client.get(
            self.view_url,
            {
                'win_id': win_advisers[0].win_id,
            }).json()

        assert len(response['results']) == 1
        self._assert_win_adviser_matches_result(win_advisers[0], response['results'][0])


class TestExportWinsBreakdownDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-breakdowns-dataset')
    factory = BreakdownFactory

    def _assert_breakdown_matches_result(self, breakdown, result):
        financial_year = get_financial_year(
            breakdown.win.date + relativedelta(years=breakdown.year - 1),
        )
        assert result == {
            'created_on': format_date_or_datetime(breakdown.created_on),
            'id': breakdown.legacy_id,
            'win__id': str(breakdown.win.id),
            'year': financial_year,
            'value': breakdown.value,
            'breakdown_type': breakdown.type.name,
        }

    def test_success(self, data_flow_api_client):
        breakdown = self.factory()

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_breakdown_matches_result(breakdown, response['results'][0])

    @pytest.mark.parametrize(
        'list_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_data(
        self,
        list_legacy_data,
        data_flow_api_client,
    ):
        if list_legacy_data:
            assert get_export_wins_legacy_data_feature_flag()

        self.factory()
        params = {
            'win': WinFactory(migrated_on=datetime.now()),
        }
        self.factory(**params)

        response = data_flow_api_client.get(self.view_url).json()
        assert len(response['results']) == (2 if list_legacy_data else 1)

    @pytest.mark.parametrize(
        'allow_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_content_override(
        self,
        allow_legacy_data,
        data_flow_api_client,
    ):
        self.factory()
        params = {
            'win': WinFactory(migrated_on=datetime.now()),
        }
        self.factory(**params)

        response = data_flow_api_client.get(
            self.view_url,
            {
                'legacy_data': allow_legacy_data,
            },
        ).json()

        assert len(response['results']) == (2 if allow_legacy_data else 1)

    def test_with_multiple_breakdowns(self, data_flow_api_client):
        breakdowns = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_breakdown_matches_result(breakdowns[i], result)

    def test_with_win_id(self, data_flow_api_client):
        breakdowns = self.factory.create_batch(3)

        response = data_flow_api_client.get(
            self.view_url,
            {
                'win_id': breakdowns[0].win_id,
            }).json()

        assert len(response['results']) == 1
        self._assert_breakdown_matches_result(
            breakdowns[0],
            response['results'][0],
        )


class TestExportWinsHVCDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-hvc-dataset')
    factory = HVCFactory

    def _assert_hvc_matches_result(self, hvc, result):
        assert result == {
            'id': hvc.legacy_id,
            'campaign_id': hvc.campaign_id,
            'financial_year': hvc.financial_year,
            'name': hvc.name,
        }

    def test_success(self, data_flow_api_client):

        hvc = HVC.objects.filter(legacy_id=1).first()

        response = data_flow_api_client.get(self.view_url).json()

        self._assert_hvc_matches_result(hvc, response['results'][0])

    def test_success_includes_legacy_hvc_items(self, data_flow_api_client):
        url = f'{self.view_url}?exclude_legacy=false&page_size=10000'
        response = data_flow_api_client.get(url).json()

        legacy_ids = [
            result['id']
            for result in response['results'] if result['id'] < EXPORT_WINS_LEGACY_ID_START_VALUE
        ]

        assert len(legacy_ids) > 0

    def test_success_excludes_legacy_hvc_items(self, data_flow_api_client):
        response = data_flow_api_client.get(
            f'{self.view_url}?exclude_legacy=true&page_size=10000',
        ).json()

        legacy_ids = [result['id'] for result in response['results']]
        assert len(legacy_ids) > 0
        assert all(
            legacy_id >= EXPORT_WINS_LEGACY_ID_START_VALUE for legacy_id in legacy_ids
        )

    def test_success_with_feature_flag(
        self,
        data_flow_api_client,
    ):
        assert get_export_wins_legacy_data_feature_flag()
        response = data_flow_api_client.get(
            f'{self.view_url}?exclude_legacy=true&page_size=10000',
        ).json()

        legacy_ids = [
            result['id']
            for result in response['results'] if result['id'] < EXPORT_WINS_LEGACY_ID_START_VALUE
        ]
        assert len(legacy_ids) > 0


class TestExportWinsWinDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-win-dataset')
    factory = WinFactory

    def _assert_win_matches_result(
        self,
        win,
        associated_programmes,
        types_of_support,
        tokens,
        result,
    ):
        contact = win.company_contacts.first()
        has_responded = win.customer_response.responded_on is not None
        expected = {
            'created_on': format_date_or_datetime(win.created_on),
            'id': str(win.id),
            'audit': None,
            'business_type': win.business_type,
            'cdms_reference': win.company.company_number,
            'company_name': win.company.name if win.migrated_on is None else win.company_name,
            'complete': len(tokens) > 0 if win.migrated_on is None else win.complete,
            'confirmation__access_to_contacts':
                win.customer_response.our_support.export_win_id if has_responded else None,
            'confirmation__access_to_information':
                win.customer_response.access_to_information.export_win_id
                if has_responded else None,
            'confirmation__agree_with_win': win.customer_response.agree_with_win,
            'confirmation__case_study_willing':
                win.customer_response.case_study_willing if has_responded else None,
            'confirmation__comments': win.customer_response.comments,
            'confirmation__company_was_at_risk_of_not_exporting':
                win.customer_response.company_was_at_risk_of_not_exporting
                if has_responded else None,
            'confirmation__created': format_date_or_datetime(
                win.customer_response.responded_on,
            ),
            'confirmation__developed_relationships':
                win.customer_response.developed_relationships.export_win_id
                if has_responded else None,
            'confirmation__gained_confidence':
                win.customer_response.gained_confidence.export_win_id if has_responded else None,
            'confirmation__has_enabled_expansion_into_existing_market':
                win.customer_response.has_enabled_expansion_into_existing_market
                if has_responded else None,
            'confirmation__has_enabled_expansion_into_new_market':
                win.customer_response.has_enabled_expansion_into_new_market
                if has_responded else None,
            'confirmation__has_explicit_export_plans':
                win.customer_response.has_explicit_export_plans if has_responded else None,
            'confirmation__has_increased_exports_as_percent_of_turnover':
                win.customer_response.has_increased_exports_as_percent_of_turnover
                if has_responded else None,
            'confirmation__improved_profile':
                win.customer_response.improved_profile.export_win_id if has_responded else None,
            'confirmation__interventions_were_prerequisite':
                win.customer_response.interventions_were_prerequisite if has_responded else None,
            'confirmation__involved_state_enterprise':
                win.customer_response.involved_state_enterprise if has_responded else None,
            'confirmation__name': contact.name
                if contact else win.customer_name if win.customer_name else None,
            'confirmation__other_marketing_source':
                win.customer_response.other_marketing_source if has_responded else None,
            'confirmation__our_support':
                win.customer_response.our_support.export_win_id if has_responded else None,
            'confirmation__overcame_problem':
                win.customer_response.overcame_problem.export_win_id if has_responded else None,
            'confirmation__support_improved_speed':
                win.customer_response.support_improved_speed if has_responded else None,
            'country': win.country.iso_alpha2_code,
            'created': format_date_or_datetime(win.created_on),
            'customer_email_address': contact.email
                if win.migrated_on is None else win.customer_email_address
                if win.customer_email_address else None,
            'customer_job_title': contact.job_title
                if win.migrated_on is None else win.customer_job_title
                if win.customer_job_title else None,
            'customer_name': contact.name
                if win.migrated_on is None else win.customer_name if win.customer_name else None,
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hvc': f'{win.hvc.campaign_id}{win.hvc.financial_year}',
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer_email_address':
                win.lead_officer.contact_email
                if win.migrated_on is None else win.lead_officer_email_address,
            'lead_officer_name':
                win.lead_officer.name
                if win.migrated_on is None else win.lead_officer_name,
            'line_manager_name': win.line_manager_name,
            'name_of_customer': win.name_of_customer,
            'name_of_export': win.name_of_export,
            'other_official_email_address': win.other_official_email_address,
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'migrated_on': format_date_or_datetime(win.migrated_on),
            'data_hub_company_id': str(win.company_id),
            'user__email': win.adviser.contact_email
                if win.migrated_on is None else win.adviser_email_address,
            'user__name': win.adviser.name if win.migrated_on is None else win.adviser_name,
            'business_potential_display': win.business_potential.name,
            'confirmation_last_export': win.customer_response.last_export.name,
            'confirmation_marketing_source': win.customer_response.marketing_source.name,
            'confirmation_portion_without_help':
                win.customer_response.expected_portion_without_help.name,
            'country_name': win.country.name,
            'customer_location_display': win.customer_location.name,
            'export_experience_display': win.export_experience.name,
            'goods_vs_services_display': win.goods_vs_services.name,
            'hq_team_display': win.hq_team.name,
            'hvo_programme_display': win.hvo_programme.name if win.hvo_programme else None,
            'sector_display': win.sector.name,
            'team_type_display': win.team_type.name,
            'num_notifications': len(tokens),
            'customer_email_date': format_date_or_datetime(
                min(tokens, key=lambda item: item.created_on).created_on,
            ) if len(tokens) > 0 else None,
        }
        max_associated_programmes = len(associated_programmes)
        for i, associated_programme in enumerate(associated_programmes):
            expected[f'associated_programme_{i+1}_display'] = associated_programme.name
        if max_associated_programmes < 5:
            for i in range(5 - max_associated_programmes):
                expected[f'associated_programme_{i+max_associated_programmes+1}_display'] = None

        max_types_of_support = len(types_of_support)
        for i, type_of_support in enumerate(types_of_support):
            expected[f'type_of_support_{i+1}_display'] = type_of_support.name
        if max_types_of_support < 3:
            for i in range(3 - max_types_of_support):
                expected[f'type_of_support_{i+max_types_of_support+1}_display'] = None

        assert result == expected

    @pytest.mark.parametrize(
        'responded',
        [True, False],
    )
    def test_success(self, data_flow_api_client, responded):
        associated_programmes = AssociatedProgrammeFactory.create_batch(3)
        types_of_support = SupportTypeFactory.create_batch(2)
        company = CompanyFactory(company_number='012345')
        contact = ContactFactory(company=company)
        win = self.factory(
            associated_programme=associated_programmes,
            type_of_support=types_of_support,
            hvo_programme=HVOProgrammesFactory(),
            company=company,
            company_contacts=[contact],
            sector_id=Sector.aerospace_assembly_aircraft.value.id,
        )
        customer_response = CustomerResponseFactory(
            win=win,
            other_marketing_source='marketing' if responded else '',
            responded_on=datetime.now() if responded else None,
        )
        tokens = CustomerResponseTokenFactory.create_batch(3, customer_response=customer_response)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_matches_result(
            win,
            associated_programmes,
            types_of_support,
            tokens,
            response['results'][0],
        )

    @pytest.mark.parametrize(
        'list_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_data(
        self,
        list_legacy_data,
        data_flow_api_client,
    ):
        if list_legacy_data:
            assert get_export_wins_legacy_data_feature_flag()
        company = CompanyFactory(company_number='012345')
        contact = ContactFactory(company=company)
        self.factory(company=company, company_contacts=[contact])
        self.factory(complete=False, migrated_on=datetime.now())
        self.factory(complete=True, migrated_on=datetime.now())

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == (3 if list_legacy_data else 1)
        if list_legacy_data:
            completes = [
                result['complete']
                for result in response['results']
                if Win.objects.get(id=result['id']).migrated_on
            ]
            assert {True, False} == set(completes)

    @pytest.mark.parametrize(
        'allow_legacy_data',
        [
            True,
            False,
        ],
    )
    def test_success_with_legacy_content_override(
        self,
        allow_legacy_data,
        data_flow_api_client,
    ):
        win = self.factory()
        contact = ContactFactory()
        win.company_contacts.add(contact)
        wins = [win]

        wins.append(
            self.factory(
                complete=False,
                migrated_on=datetime.now(),
                customer_email_address='test@customer',
                customer_name='John Doe',
                customer_job_title='Tester',
                company_name='Company A',
            ),
        )
        wins.append(
            self.factory(
                complete=True,
                migrated_on=datetime.now(),
                customer_email_address='test@customer',
                customer_name='John Doe',
                customer_job_title='Tester',
                company_name='Company B',
            ),
        )

        CustomerResponseFactory.create_batch(len(wins), win=Iterator(wins))

        response = data_flow_api_client.get(
            self.view_url,
            {
                'legacy_data': allow_legacy_data,
            },
        ).json()

        assert len(response['results']) == (3 if allow_legacy_data else 1)
        for i, result in enumerate(response['results']):
            self._assert_win_matches_result(
                wins[i],
                [],
                [],
                [],
                result,
            )

    def test_customer_email_date_uses_earliest(self, data_flow_api_client):
        win = self.factory()
        customer_response = CustomerResponseFactory(win=win)
        created_on = date.today()
        with freeze_time(created_on) as frozen_time:
            CustomerResponseTokenFactory(
                customer_response=customer_response,
            )

            frozen_time.move_to(created_on - timedelta(days=1))
            CustomerResponseTokenFactory(
                customer_response=customer_response,
            )

            frozen_time.move_to(created_on - timedelta(days=7))
            customer_response_earliest = CustomerResponseTokenFactory(
                customer_response=customer_response,
            )

        response = data_flow_api_client.get(self.view_url).json()
        assert response['results'][0]['customer_email_date'] == format_date_or_datetime(
            customer_response_earliest.created_on,
        )
