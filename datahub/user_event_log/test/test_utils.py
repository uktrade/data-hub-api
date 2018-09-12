from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory
from datahub.user_event_log.constants import USER_EVENT_TYPES
from datahub.user_event_log.utils import record_user_event


@pytest.mark.parametrize(
    'data,expected_data',
    (
        (None, None),
        (
            {'a': 'b'},
            {'a': 'b'}
        ),
        (
            {'a': datetime(2016, 10, 10, 1, 0, 2, tzinfo=utc)},
            {'a': '2016-10-10T01:00:02Z'}
        ),
        (
            {'a': UUID('73c18056-c592-478b-baf9-3b1322dd0dcf')},
            {'a': '73c18056-c592-478b-baf9-3b1322dd0dcf'}
        ),
        ('string', 'string'),
        ([0, 2, 3], [0, 2, 3]),
    )
)
@pytest.mark.django_db
def test_record_user_event(data, expected_data):
    """Test record_user_event() for various model and data values."""
    adviser = AdviserFactory()
    request = Mock(user=adviser, path='test-path')
    event = record_user_event(request, USER_EVENT_TYPES.search_export, data=data)
    event.refresh_from_db()

    assert event.adviser == adviser
    assert event.type == USER_EVENT_TYPES.search_export
    assert event.api_url_path == 'test-path'
    assert event.data == expected_data
