import pytest

from django.urls import reverse

from datahub.core.test_utils import (
    format_date_or_datetime,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.export_win.models import HVC

from datahub.export_win.test.factories import (
    AssociatedProgrammeFactory,
    BreakdownFactory,
    CustomerResponseFactory,
    HVCFactory,
    HVOProgrammesFactory,
    SupportTypeFactory,
    WinAdviserFactory,
    WinFactory,
)


pytestmark = pytest.mark.django_db


class TestExportWinsAdvisersDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-advisers-dataset')
    factory = WinAdviserFactory

    def _assert_win_adviser_matches_result(self, win_adviser, result):
        assert result == {
            'created_on': format_date_or_datetime(win_adviser.created_on),
            'id': win_adviser.legacy_id,
            'location': win_adviser.location,
            'name': win_adviser.name,
            'win__id': str(win_adviser.win.id),
            'hq_team_display': win_adviser.hq_team.name,
            'team_type_display': win_adviser.team_type.name,
            'hq_team': win_adviser.hq_team.export_win_id,
            'team_type': win_adviser.team_type.export_win_id,
        }

    def test_success(self, data_flow_api_client):

        win_adviser = self.factory(location='Somewhere', name='bob')

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_adviser_matches_result(win_adviser, response['results'][0])

    def test_with_multiple_win_adviser(self, data_flow_api_client):

        win_advisers = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_win_adviser_matches_result(win_advisers[i], result)


class TestExportWinsBreakdownDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-breakdowns-dataset')
    factory = BreakdownFactory

    def _assert_breakdown_matches_result(self, breakdown, result):
        assert result == {
            'created_on': format_date_or_datetime(breakdown.created_on),
            'id': breakdown.legacy_id,
            'win__id': str(breakdown.win.id),
            'year': breakdown.year,
            'value': breakdown.value,
            'breakdown_type': breakdown.type.name,
        }

    def test_success(self, data_flow_api_client):

        breakdown = self.factory()

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_breakdown_matches_result(breakdown, response['results'][0])

    def test_with_multiple_breakdowns(self, data_flow_api_client):

        breakdowns = self.factory.create_batch(3)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 3
        for i, result in enumerate(response['results']):
            self._assert_breakdown_matches_result(breakdowns[i], result)


class TestExportWinsHVCDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-hvc-dataset')
    factory = HVCFactory

    def _assert_hvc_matches_result(self, hvc, result):
        assert result == {
            'id': hvc.legacy_id,
            'campaign_id': hvc.campaign_id,
            'financial_year': hvc.financial_year,
            'name': hvc.export_win_id,
        }

    def test_success(self, data_flow_api_client):

        hvc = HVC.objects.filter(legacy_id=1).first()

        response = data_flow_api_client.get(self.view_url).json()

        self._assert_hvc_matches_result(hvc, response['results'][0])


class TestExportWinsWinDatasetView(BaseDatasetViewTest):
    view_url = reverse('api-v4:dataset:export-wins-win-dataset')
    factory = WinFactory

    def _assert_win_matches_result(
        self,
        win,
        associated_programmes,
        types_of_support,
        result,
    ):
        expected = {
            'created_on': format_date_or_datetime(win.created_on),
            'id': str(win.id),
            'audit': win.audit,
            'business_type': win.business_type,
            'cdms_reference': win.cdms_reference,
            'company_name': win.company.name,
            'complete': win.complete,
            'confirmation__access_to_contacts': win.customer_response.our_support.export_win_id,
            'confirmation__access_to_information':
                win.customer_response.access_to_information.export_win_id,
            'confirmation__agree_with_win': win.customer_response.agree_with_win,
            'confirmation__case_study_willing': win.customer_response.case_study_willing,
            'confirmation__comments': win.customer_response.comments,
            'confirmation__company_was_at_risk_of_not_exporting':
                win.customer_response.company_was_at_risk_of_not_exporting,
            'confirmation__created': format_date_or_datetime(
                win.customer_response.created_on,
            ),
            'confirmation__developed_relationships':
                win.customer_response.developed_relationships.export_win_id,
            'confirmation__gained_confidence':
                win.customer_response.gained_confidence.export_win_id,
            'confirmation__has_enabled_expansion_into_existing_market':
                win.customer_response.has_enabled_expansion_into_existing_market,
            'confirmation__has_enabled_expansion_into_new_market':
                win.customer_response.has_enabled_expansion_into_new_market,
            'confirmation__has_explicit_export_plans':
                win.customer_response.has_explicit_export_plans,
            'confirmation__has_increased_exports_as_percent_of_turnover':
                win.customer_response.has_increased_exports_as_percent_of_turnover,
            'confirmation__improved_profile': win.customer_response.improved_profile.export_win_id,
            'confirmation__interventions_were_prerequisite':
                win.customer_response.interventions_were_prerequisite,
            'confirmation__involved_state_enterprise':
                win.customer_response.involved_state_enterprise,
            'confirmation__name': win.customer_response.name,
            'confirmation__other_marketing_source': win.customer_response.other_marketing_source,
            'confirmation__our_support': win.customer_response.our_support.export_win_id,
            'confirmation__overcame_problem': win.customer_response.overcame_problem.export_win_id,
            'confirmation__support_improved_speed': win.customer_response.support_improved_speed,
            'country': win.country.iso_alpha2_code,
            'created': format_date_or_datetime(win.created_on),
            'customer_email_address': win.customer_email_address,
            'customer_job_title': win.customer_job_title,
            'customer_name': win.customer_name,
            'date': format_date_or_datetime(win.date),
            'description': win.description,
            'has_hvo_specialist_involvement': win.has_hvo_specialist_involvement,
            'hvc': win.hvc.export_win_id,
            'is_e_exported': win.is_e_exported,
            'is_line_manager_confirmed': win.is_line_manager_confirmed,
            'is_personally_confirmed': win.is_personally_confirmed,
            'is_prosperity_fund_related': win.is_prosperity_fund_related,
            'lead_officer_email_address': win.lead_officer_email_address,
            'lead_officer_name': win.lead_officer_name,
            'line_manager_name': win.line_manager_name,
            'name_of_customer': win.name_of_customer,
            'name_of_export': win.name_of_export,
            'other_official_email_address': win.other_official_email_address,
            'total_expected_export_value': win.total_expected_export_value,
            'total_expected_non_export_value': win.total_expected_non_export_value,
            'total_expected_odi_value': win.total_expected_odi_value,
            'user__email': win.adviser.email,
            'user__name': win.adviser.name,
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
            'hvo_programme_display': win.hvo_programme.name,
            'sector_display': win.sector.segment,
            'team_type_display': win.team_type.name,
        }
        for i, associated_programme in enumerate(associated_programmes):
            expected[f'associated_programme_{i+1}_display'] = associated_programme.name
        for i, type_of_support in enumerate(types_of_support):
            expected[f'type_of_support_{i+1}_display'] = type_of_support.name

        assert result == expected

    def test_success(self, data_flow_api_client):
        associated_programmes = AssociatedProgrammeFactory.create_batch(3)
        types_of_support = SupportTypeFactory.create_batch(2)
        win = self.factory(
            associated_programme=associated_programmes,
            type_of_support=types_of_support,
            hvo_programme=HVOProgrammesFactory(),
        )
        CustomerResponseFactory(win=win)

        response = data_flow_api_client.get(self.view_url).json()

        assert len(response['results']) == 1
        self._assert_win_matches_result(
            win,
            associated_programmes,
            types_of_support,
            response['results'][0],
        )
