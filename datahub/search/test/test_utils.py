from unittest.mock import Mock

from datahub.search.utils import get_model_copy_to_target_field_names


def test_get_model_copy_to_field_names(monkeypatch):
    """Test that get_model_copy_to_field_names handles() handles various copy_to forms."""
    monkeypatch.setattr('datahub.search.utils.get_model_fields', Mock(
        return_value={
            'field1': Mock(spec_set=()),
            'field2': Mock(spec_set=('copy_to',), copy_to='copy_to_str'),
            'field3': Mock(spec_set=('copy_to',), copy_to=['copy_to_list1', 'copy_to_list2']),
        }
    ))
    assert get_model_copy_to_target_field_names(Mock()) == {
        'copy_to_str',
        'copy_to_list1',
        'copy_to_list2',
    }
