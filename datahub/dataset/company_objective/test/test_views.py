import pytest
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import ObjectiveFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest


def get_expected_data_from_company_objective(objective):
    """Returns company objective data as a dictionary"""
    return {
        'id': str(objective.id),
        'company_id': str(objective.company_id),
        'subject': objective.subject,
        'detail': objective.detail,
        'target_date': format_date_or_datetime(objective.target_date),
        'has_blocker': objective.has_blocker,
        'blocker_description': objective.blocker_description,
        'progress': objective.progress,
        'created_on': format_date_or_datetime(objective.created_on),
        'modified_on': format_date_or_datetime(objective.modified_on),
        'created_by_id': str(objective.created_by_id),
        'modified_by_id': str(objective.modified_by_id),
    }


@pytest.mark.django_db
class TestCompanyObjectiveDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for CompanyObjectiveDatasetView
    """

    view_url = reverse('api-v4:dataset:company-objective-dataset')
    factory = ObjectiveFactory

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single pipeline item"""
        objective = ObjectiveFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        response_results = response.json()['results']
        assert len(response_results) == 1

        result = response_results[0]
        expected_result = get_expected_data_from_company_objective(objective)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records"""
        [objective1, objective2, objective3, objective4] = ObjectiveFactory.create_batch(4)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4

        expected_list = [objective1, objective2, objective3, objective4]
        for index, item in enumerate(expected_list):
            assert str(item.id) == response_results[index]['id']
