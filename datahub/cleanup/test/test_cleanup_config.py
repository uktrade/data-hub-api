from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.timezone import utc
from freezegun import freeze_time

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter


FROZEN_TIME = datetime(2018, 6, 1, 2, tzinfo=utc)


@freeze_time(FROZEN_TIME)
class TestCleanupFilter:
    """Tests DatetimeLessThanCleanupFilter."""

    @pytest.mark.parametrize(
        'age_threshold,expected_datetime',
        (
            (
                relativedelta(years=10),
                datetime(2008, 6, 1, 0, tzinfo=utc),
            ),
            (
                datetime(2012, 8, 3, 5, tzinfo=utc),
                datetime(2012, 8, 3, 5, tzinfo=utc),
            ),
        ),
    )
    def test_as_q(self, age_threshold, expected_datetime):
        """
        Test that the cut_off_date property calculates the cut-off date for both
        a relativedelta and an absolute datetime.
        """
        cleanup_filter = DatetimeLessThanCleanupFilter('date', age_threshold)
        assert cleanup_filter.cut_off_date == expected_datetime

    @pytest.mark.parametrize(
        'include_null,expected_q',
        (
            (
                False,
                Q(date__lt=datetime(2008, 6, 1, 0, tzinfo=utc)),
            ),
            (
                True,
                Q(date__lt=datetime(2008, 6, 1, 0, tzinfo=utc)) | Q(date__isnull=True),
            ),
        ),
    )
    def test_cut_off_date(self, include_null, expected_q):
        """Test that the expected Q objects are generated."""
        cleanup_filter = DatetimeLessThanCleanupFilter(
            'date',
            relativedelta(years=10),
            include_null=include_null,
        )
        assert cleanup_filter.as_q() == expected_q
