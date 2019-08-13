from collections import Counter

import pytest

from datahub.search.utils import get_unique_values_and_exclude_nulls_from_list


@pytest.mark.parametrize(
    'data,expected_result',
    (
        (
            [1], [1],
        ),
        (
            [1, 1, 2, 1], [1, 2],
        ),
        (
            [None, 1, 2, None, 2], [1, 2],
        ),
        (
            [None], [],
        ),
    ),
)
def test_get_unique_values_and_exclude_nulls_from_list(data, expected_result):
    """Test given a list of values filter unique and remove null values."""
    assert Counter(get_unique_values_and_exclude_nulls_from_list(data)) == Counter(expected_result)
