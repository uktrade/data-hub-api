from datetime import date

import pytest
from freezegun import freeze_time

from datahub.investment.validate import (
    _is_provided_and_is_date_in_the_past,
    is_provided_and_is_date_less_than_a_year_ago,
)


@pytest.mark.parametrize(
    'data_date,expected_result',
    (
        (
            date(2019, 2, 2),
            False,
        ),
        (
            date(2019, 2, 1),
            True,
        ),
        (
            date(2019, 1, 31),
            True,
        ),
        (
            None,
            False,
        ),
    ),

)
@freeze_time('2019-02-01')
def test_is_date_in_the_past(data_date, expected_result):
    """Tests that a given date is in the past."""
    assert _is_provided_and_is_date_in_the_past(data_date) is expected_result


@pytest.mark.parametrize(
    'post_data,expected_result',
    (
        (
            date(2019, 2, 1),
            True,
        ),
        (
            date(2019, 2, 2),
            False,
        ),
        (
            date(2019, 1, 31),
            True,
        ),
        (
            date(2017, 9, 30),
            False,
        ),
        (
            None,
            False,
        ),
        (
            {},
            False,
        ),
    ),

)
@freeze_time('2019-02-01')
def test_is_date_less_than_a_year_ago(post_data, expected_result):
    """Tests if a given date is within the last year."""
    assert is_provided_and_is_date_less_than_a_year_ago(post_data) is expected_result
