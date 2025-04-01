from datetime import datetime, timezone

import pytest

from datahub.investment_lead.test.utils import assert_datetimes


class TestAssertDatetimes:
    def test_same_datetime_objects(self):
        dt = datetime(2024, 10, 14, 0, 0, tzinfo=timezone.utc)
        assert_datetimes(dt, dt)

    def test_same_strings_with_microseconds(self):
        dt_string = '2024-10-14T12:00:00.123456Z'
        assert_datetimes(dt_string, dt_string)

    def test_same_string_without_microseconds(self):
        dt_string = '2024-10-14T12:00:00Z'
        assert_datetimes(dt_string, dt_string)

    def test_different_strings_one_with_microseconds(self):
        dt_string = '2024-10-14T12:00:00Z'
        dt_string_with_microseconds = '2024-10-14T12:00:00.123456Z'
        with pytest.raises(AssertionError):
            assert_datetimes(dt_string, dt_string_with_microseconds)

    def test_different_strings_with_microseconds(self):
        dt_string_1 = '2024-10-14T12:00:00.123456Z'
        dt_string_2 = '2024-10-14T14:00:00.123456Z'
        with pytest.raises(AssertionError):
            assert_datetimes(dt_string_1, dt_string_2)

    def test_different_strings_without_microseconds(self):
        dt_string_1 = '2024-10-14T12:00:00Z'
        dt_string_2 = '2024-10-14T14:00:00Z'
        with pytest.raises(AssertionError):
            assert_datetimes(dt_string_1, dt_string_2)

    def test_different_formats(self):
        dt_string = '2024-10-14T12:00:00Z'
        dt = datetime(2024, 10, 14, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(AssertionError):
            assert_datetimes(dt_string, dt)

    def test_missing_timezone(self):
        dt1 = datetime(2024, 10, 14, 0, 0)
        dt2 = datetime(2024, 10, 14, 0, 0, tzinfo=timezone.utc)
        assert_datetimes(dt1, dt2)
