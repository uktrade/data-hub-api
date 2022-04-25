from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from django.urls import reverse
from django.utils.timezone import utc
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import format_date_or_datetime
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event


def get_expected_data_from_user_log(event):
    """Returns user event log data as a dictionary"""
    return {
        'adviser__id': str(event.adviser.id),
        'type': event.type,
        'api_url_path': event.api_url_path,
        'created_on': format_date_or_datetime(event.timestamp),
    }


@pytest.mark.django_db
class TestUserEventsViewSet:
    """
    Tests for the user event logs dataset endpoint
    """

    factory = AdviserFactory
    view_url = reverse('api-v4:dataset:user-events-dataset')

    @pytest.mark.parametrize(
        'data',
        (
            (None, None),
            (
                {'a': 'b'},
                {'a': 'b'},
            ),
            (
                {'a': datetime(2016, 10, 10, 1, 0, 2, tzinfo=utc)},
                {'a': '2016-10-10T01:00:02Z'},
            ),
            (
                {'a': UUID('73c18056-c592-478b-baf9-3b1322dd0dcf')},
                {'a': '73c18056-c592-478b-baf9-3b1322dd0dcf'},
            ),
            ('string', 'string'),
            ([0, 2, 3], [0, 2, 3]),
        ),
    )
    def test_success(self, data, data_flow_api_client):
        """Test that endpoint returns with expected data for a single user event"""
        request = Mock(user=self.factory(), path='test-path')
        event = record_user_event(request, UserEventType.SEARCH_EXPORT, data=data)
        event.refresh_from_db()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_user_log(event)
        assert result == expected_result
