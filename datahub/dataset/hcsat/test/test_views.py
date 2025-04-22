from datetime import datetime, timezone

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test_utils import format_date_or_datetime
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.hcsat.test.factories import CustomerSatisfactionToolFeedbackFactory


def get_expected_data_from_hcsat(feedback):
    """Returns HCSAT feedback data as a dictionary."""
    return {
        'id': str(feedback.id),
        'created_on': format_date_or_datetime(feedback.created_on),
        'modified_on': format_date_or_datetime(feedback.modified_on),
        'url': feedback.url,
        'was_useful': feedback.was_useful,
        'did_not_find_what_i_wanted': feedback.did_not_find_what_i_wanted,
        'difficult_navigation': feedback.difficult_navigation,
        'lacks_feature': feedback.lacks_feature,
        'unable_to_load': feedback.unable_to_load,
        'inaccurate_information': feedback.inaccurate_information,
        'other_issues': feedback.other_issues,
        'other_issues_detail': feedback.other_issues_detail,
        'improvement_suggestion': feedback.improvement_suggestion,
    }


@pytest.mark.django_db
class TestHCSATDatasetViewSet(BaseDatasetViewTest):
    """Tests for HCSATDatasetView."""

    view_url = reverse('api-v4:dataset:hcsat-dataset')
    factory = CustomerSatisfactionToolFeedbackFactory

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single feedback entry."""
        feedback = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_hcsat(feedback)
        assert result == expected_result

    def test_with_multiple_records(self, data_flow_api_client):
        """Test that endpoint returns correct number of records in expected order."""
        with freeze_time('2025-01-01 12:30:00'):
            feedback_1 = self.factory()
        with freeze_time('2025-01-03 12:00:00'):
            feedback_2 = self.factory()
        with freeze_time('2025-01-01 12:00:00'):
            feedback_3 = self.factory()
            feedback_4 = self.factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4

        # default ordering is ('created_on', 'pk')
        expected_list = sorted([feedback_3, feedback_4], key=lambda x: x.pk) + [
            feedback_1,
            feedback_2,
        ]
        assert [res['id'] for res in response_results] == [str(item.id) for item in expected_list]

    def test_with_updated_since_filter(self, data_flow_api_client):
        """Test that the endpoint returns only records modified after a certain date."""
        with freeze_time('2025-01-01 12:30:00'):
            self.factory()
        with freeze_time('2025-03-01 12:30:00'):
            feedback_after = self.factory()

        updated_since_date = datetime(2025, 2, 1, tzinfo=timezone.utc).strftime('%Y-%m-%d')
        response = data_flow_api_client.get(self.view_url, {'updated_since': updated_since_date})

        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == 1
        assert results[0]['id'] == str(feedback_after.id)
