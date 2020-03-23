import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    EventServiceDeliveryFactory,
    InteractionExportCountryFactory,
    InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)


def get_expected_data_from_interaction(interaction):
    """Returns expected API response dictionary for an interaction"""
    return {
        'adviser_ids': [
            str(x.adviser_id)
            for x in interaction.dit_participants.all().order_by('pk')
        ],
        'communication_channel__name': get_attr_or_none(
            interaction,
            'communication_channel.name',
        ),
        'company_id': str(interaction.company.id),
        'contact_ids': [str(x.id) for x in interaction.contacts.all().order_by('pk')],
        'created_by_id': str(interaction.created_by_id),
        'created_on': format_date_or_datetime(interaction.created_on),
        'date': format_date_or_datetime(interaction.date),
        'event_id': (
            str(interaction.event_id)
            if interaction.event_id is not None
            else None
        ),
        'grant_amount_offered': (
            float(interaction.grant_amount_offered)
            if interaction.grant_amount_offered is not None
            else None
        ),
        'id': str(interaction.id),
        'interaction_link': interaction.get_absolute_url(),
        'investment_project_id': (
            str(interaction.investment_project_id)
            if interaction.investment_project is not None
            else None
        ),
        'kind': interaction.kind,
        'modified_on': format_date_or_datetime(interaction.modified_on),
        'net_company_receipt': (
            float(interaction.net_company_receipt)
            if interaction.net_company_receipt is not None
            else None
        ),
        'notes': interaction.notes,
        'policy_area_names': (
            [x.name for x in interaction.policy_areas.all()]
            if interaction.policy_areas.exists() else None
        ),
        'policy_feedback_notes': interaction.policy_feedback_notes,
        'policy_issue_type_names': (
            [x.name for x in interaction.policy_issue_types.all()]
            if interaction.policy_areas.exists() else None
        ),
        'sector': get_attr_or_none(interaction, 'company.sector.name'),
        'service_delivery_status__name': get_attr_or_none(
            interaction,
            'service_delivery_status.name',
        ),
        'service_delivery': get_attr_or_none(interaction, 'service.name'),
        'subject': interaction.subject,
        'theme': interaction.theme,
    }


def get_expected_data_from_interaction_export_country(interaction_export_country):
    """Returns expected API response dictionary for an interaction_export_country"""    
    return {
        'country__iso_alpha2_code': interaction_export_country.country.iso_alpha2_code,
        'country__name': interaction_export_country.country.name,
        'created_on': format_date_or_datetime(interaction_export_country.created_on),
        'id': str(interaction_export_country.id),
        'interaction__company_id': str(interaction_export_country.interaction.company_id),
        'interaction__id': str(interaction_export_country.interaction_id),
        'status': interaction_export_country.status,
    }


@pytest.mark.django_db
class TestInteractionsDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for InteractionsDatasetView
    """

    view_url = reverse('api-v4:dataset:interactions-dataset')
    factory = CompanyInteractionFactory

    @pytest.mark.parametrize(
        'interaction_factory', (
            CompanyInteractionFactory,
            CompanyInteractionFactoryWithPolicyFeedback,
            EventServiceDeliveryFactory,
            InvestmentProjectInteractionFactory,
            ServiceDeliveryFactory,
        ),
    )
    def test_success(self, data_flow_api_client, interaction_factory):
        """Test that endpoint returns with expected data for a single interaction"""
        interaction = interaction_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_interaction(interaction)
        assert result == expected_result

    def test_with_multiple_interactions(self, data_flow_api_client):
        """Test that the correct number of records are returned in the right order"""
        with freeze_time('2019-01-01 12:30:00'):
            interaction1 = CompanyInteractionFactory()
        with freeze_time('2019-01-03 12:00:00'):
            interaction2 = CompanyInteractionFactory()
        with freeze_time('2019-01-01 12:00:00'):
            interaction3 = CompanyInteractionFactory()
            interaction4 = CompanyInteractionFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted(
            [interaction3, interaction4],
            key=lambda item: item.pk,
        ) + [interaction1, interaction2]
        for index, interaction in enumerate(expected_list):
            assert interaction.get_absolute_url() == response_results[index]['interaction_link']


@pytest.mark.django_db
class TestInteractionsExportCountryDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for InteractionsExportCountryDatasetView
    """

    view_url = reverse('api-v4:dataset:interactions-export-country-dataset')
    factory = InteractionExportCountryFactory

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single interaction"""
        interaction_export_country = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_interaction_export_country(
            interaction_export_country,
        )
        assert result == expected_result

    def test_with_multiple_interactions(self, data_flow_api_client):
        """Test that the correct number of records are returned in the right order"""
        with freeze_time('2019-01-01 12:30:00'):
            interaction_export_country_1 = self.factory()
        with freeze_time('2019-01-03 12:00:00'):
            interaction_export_country_2 = self.factory()
        with freeze_time('2019-01-01 12:00:00'):
            interaction_export_country_3 = self.factory()
            interaction_export_country_4 = self.factory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_list = sorted(
            [interaction_export_country_3, interaction_export_country_4],
            key=lambda item: item.id,
        ) + [interaction_export_country_1, interaction_export_country_2]
        for index, interaction_export_country in enumerate(expected_list):
            expected_result = get_expected_data_from_interaction_export_country(
                interaction_export_country,
            )
            assert expected_result['id'] == response_results[index]['id']
