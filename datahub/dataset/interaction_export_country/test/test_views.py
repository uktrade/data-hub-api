import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.interaction.test.factories import InteractionExportCountryFactory


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
