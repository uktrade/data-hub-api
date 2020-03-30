from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.utils import record_user_event


@pytest.mark.django_db
class TestRecordUserEvent:
    """Test record_user_event()."""

    @pytest.mark.parametrize(
        'data,expected_data',
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
    def test_records_data(self, data, expected_data):
        """Test various data values."""
        adviser = AdviserFactory()
        request = Mock(user=adviser, path='test-path')
        event = record_user_event(request, UserEventType.SEARCH_EXPORT, data=data)
        event.refresh_from_db()

        assert event.adviser == adviser
        assert event.type == UserEventType.SEARCH_EXPORT
        assert event.api_url_path == 'test-path'
        assert event.data == expected_data
