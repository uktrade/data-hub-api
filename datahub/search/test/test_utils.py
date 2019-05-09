from collections import Counter
from unittest.mock import Mock

import pytest

from datahub.search.utils import (
    get_model_copy_to_target_field_names,
    get_unique_values_and_exclude_nulls_from_list,
)


def test_get_model_copy_to_field_names(monkeypatch):
    """Test that get_model_copy_to_field_names handles() handles various copy_to forms."""
    monkeypatch.setattr(
        'datahub.search.utils.get_model_fields',
        Mock(
            return_value={
                'field1': Mock(spec_set=()),
                'field2': Mock(spec_set=('copy_to',), copy_to='copy_to_str'),
                'field3': Mock(spec_set=('copy_to',), copy_to=['copy_to_list1', 'copy_to_list2']),
            },
        ),
    )
    assert get_model_copy_to_target_field_names(Mock()) == {
        'copy_to_str',
        'copy_to_list1',
        'copy_to_list2',
    }


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
