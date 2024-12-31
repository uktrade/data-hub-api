from datetime import datetime, timezone

import pytest
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.investment_lead.test.factories import EYBLeadFactory


def get_expected_data_from_eyb(eyb_lead):
    """Returns EYB Lead data as a dictionary"""
    investment_projects = eyb_lead.investment_projects.all().order_by(
        'name',
        'id',
    )
    # TODO MK ensure empty array is returned rather than [None, ]
    investment_project_ids = [str(investment_project.id) for investment_project in investment_projects]
    if investment_project_ids == []:
        investment_project_ids = [None, ]
    #     ? investment_projects.len else 
    # ? eyb_lead.investment_projects.all().len else investment_projects.objects.none(),

    data = {
        'modified_on': format_date_or_datetime(eyb_lead.modified_on),
        # Triage component
        'triage_hashed_uuid': str(eyb_lead.triage_hashed_uuid),
        'triage_created': format_date_or_datetime(eyb_lead.triage_created),
        'triage_modified': format_date_or_datetime(eyb_lead.triage_modified),
        'sector': str(eyb_lead.sector.id) if eyb_lead.sector else None,
        'sector_segments': eyb_lead.sector_segments,
        'intent': eyb_lead.intent,
        'intent_other': eyb_lead.intent_other,
        'proposed_investment_region': str(eyb_lead.proposed_investment_region.id) if eyb_lead.proposed_investment_region else None,
        'proposed_investment_city': eyb_lead.proposed_investment_city,
        'proposed_investment_location_none': eyb_lead.proposed_investment_location_none,
        'hiring': eyb_lead.hiring,
        'spend': eyb_lead.spend,
        'spend_other': eyb_lead.spend_other,
        'is_high_value': eyb_lead.is_high_value,

        # User component
        'user_hashed_uuid': eyb_lead.user_hashed_uuid,
        'user_created': format_date_or_datetime(eyb_lead.user_created),
        'user_modified': format_date_or_datetime(eyb_lead.user_modified),
        'company_name': eyb_lead.company_name,
        'duns_number': eyb_lead.duns_number,
        'address_1': eyb_lead.address_1,
        'address_2': eyb_lead.address_2,
        'address_town': eyb_lead.address_town,
        'address_county': eyb_lead.address_county,
        'address_country': str(eyb_lead.address_country.id) if eyb_lead.address_country else None,
        'address_postcode': eyb_lead.address_postcode,
        'company_website': eyb_lead.company_website,
        'full_name': eyb_lead.full_name,
        'role': eyb_lead.role,
        'email': eyb_lead.email,
        'telephone_number': eyb_lead.telephone_number,
        'agree_terms': eyb_lead.agree_terms,
        'agree_info_email': eyb_lead.agree_info_email,
        'landing_timeframe': eyb_lead.landing_timeframe,
        'company': str(eyb_lead.company.id) if eyb_lead.company else None,
        'investment_project_ids': investment_project_ids,

        # Marketing component
        'marketing_hashed_uuid': eyb_lead.marketing_hashed_uuid,
        'utm_name': eyb_lead.utm_name,
        'utm_source': eyb_lead.utm_source,
        'utm_medium': eyb_lead.utm_medium,
        'utm_content': eyb_lead.utm_content,

        # 'created_on': format_date_or_datetime(eyb_lead.created_on),
        # 'created_by_id': str(eyb_lead.created_by_id),
        # 'modified_on': format_date_or_datetime(eyb_lead.modified_on),
        # 'modified_by_id': str(eyb_lead.modified_by_id) if eyb_lead.modified_by else None,
        # 'archived': eyb_lead.archived,
        # 'archived_on': format_date_or_datetime(eyb_lead.archived_on),
        # 'archived_by_id': str(eyb_lead.archived_by_id) if eyb_lead.archived_by else None,
        # 'archived_reason': eyb_lead.archived_reason,
        # 'id': str(eyb_lead.id),
        # 'title': eyb_lead.title,
        # 'description': eyb_lead.description,
        # 'due_date': format_date_or_datetime(eyb_lead.due_date),
        # 'reminder_days': eyb_lead.reminder_days,
        # 'email_reminders_enabled': eyb_lead.email_reminders_enabled,
        # 'adviser_ids': [str(adviser.id) for adviser in eyb_lead.advisers.all().order_by(
        #     'first_name',
        #     'id',
        # )],
        # 'reminder_date': eyb_lead.reminder_date,
        # 'investment_project_id': str(eyb_lead.investment_project.id)
        # if eyb_lead.investment_project else None,
        # 'company_id': str(eyb_lead.company.id) if eyb_lead.company else None,
        # 'interaction_id': str(eyb_lead.interaction.id) if eyb_lead.interaction else None,
        # 'status': eyb_lead.status.value,
    }
    return data


@pytest.mark.django_db
class TestEYBDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for EYBDatasetView
    """

    view_url = reverse('api-v4:dataset:expand-your-business-dataset')
    factory = EYBLeadFactory

    def test_success_with_one(self, data_flow_api_client):
        """Test that the endpoint returns expected data for a single eyb lead."""
        eyb_lead = self.factory(
        )
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        results_from_response = response.json()['results']
        assert len(results_from_response) == 1

        eyb_lead_from_response = results_from_response[0]
        expected_eyb_lead = get_expected_data_from_eyb(eyb_lead)
        assert eyb_lead_from_response == expected_eyb_lead

    def test_success_with_multiple(self, data_flow_api_client):
        """Test that the endpoint returns expected data for multiple EYB leads."""
        eyb_lead_one = self.factory(
            # investment_projects=InvestmentProjectFactory.create_batch(1),
        )
        eyb_lead_two = self.factory(
            company=CompanyFactory(),
        )

        eyb_lead_three = self.factory(
            # interaction=InteractionFactoryBase(),
        )
        eyb_lead_four = self.factory(
            investment_projects=InvestmentProjectFactory.create_batch(3),
        )

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        results_from_response = response.json()['results']
        assert len(results_from_response) == 4

        eyb_leads_from_response = results_from_response
        expected_eyb_leads = [
            get_expected_data_from_eyb(eyb_lead)
            for eyb_lead
            in [eyb_lead_one, eyb_lead_two, eyb_lead_three, eyb_lead_four]
        ]
        assert eyb_leads_from_response == expected_eyb_leads

# def test_investment_projects
# none, single, multiple

