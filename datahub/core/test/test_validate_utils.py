from unittest.mock import MagicMock, Mock

import pytest

from datahub.core import validate_utils
from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank


@pytest.mark.parametrize('value,blank', (
    (None, True),
    ('', True),
    ([], True),
    (0, False),
    (2323, False),
    ('dfdf', False),
    ([1234], False),
))
def test_is_blank(value, blank):
    """Tests is_blank() for various values."""
    assert is_blank(value) == blank


@pytest.mark.parametrize('value,blank', (
    (None, False),
    ('', False),
    ([], False),
    (0, True),
    (2323, True),
    ('dfdf', True),
    ([1234], True),
))
def test_is_not_blank(value, blank):
    """Tests is_not_blank() for various values."""
    assert is_not_blank(value) == blank


class TestDataCombiner:
    """Data Combiner tests."""

    def test_is_field_to_many_for_to_many_field(self, monkeypatch):
        """Tests that test_is_field_to_many() returns True for a to-many field."""
        instance = Mock()
        model = Mock()
        mock_field_info = Mock(
            relations={
                'field1': Mock(to_many=True),
            }
        )
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert data_combiner.is_field_to_many('field1')

    def test_is_field_to_many_for_non_to_many_relation(self, monkeypatch):
        """Tests that test_is_field_to_many() returns False for a non-to-many relation."""
        instance = Mock()
        model = Mock()
        mock_field_info = Mock(
            relations={
                'field1': Mock(to_many=False),
            }
        )
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert not data_combiner.is_field_to_many('field1')

    def test_is_field_to_many_for_normal_field(self, monkeypatch):
        """Tests that test_is_field_to_many() returns False for a normal field."""
        instance = Mock()
        model = Mock()
        mock_field_info = Mock(relations={})
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert not data_combiner.is_field_to_many('field1')

    def test_get_value_instance(self):
        """Tests getting a simple value from an instance."""
        instance = Mock(field1=1, field2=2)
        data = {'field2': 456}
        data_combiner = DataCombiner(instance, data)
        assert data_combiner.get_value('field1') == 1

    def test_get_value_data(self):
        """Tests getting a simple value from update data."""
        instance = Mock(field1=1, field2=2)
        data = {'field2': 456}
        data_combiner = DataCombiner(instance, data)
        assert data_combiner.get_value('field2') == 456

    def test_get_value_to_many_instance(self):
        """Tests getting a to-many value from an instance."""
        instance = Mock(field1=MagicMock())
        instance.field1.all.return_value = [123]
        data_combiner = DataCombiner(instance, None)
        assert data_combiner.get_value_to_many('field1') == [123]

    def test_get_value_to_many_data(self):
        """Tests getting a to-many value from update data."""
        instance = Mock(field1=MagicMock())
        data = {'field1': [123]}
        data_combiner = DataCombiner(instance, data)
        assert data_combiner.get_value_to_many('field1') == data['field1']

    def test_get_value_id_instance(self):
        """Tests getting a foreign key from an instance."""
        subinstance = Mock()
        subinstance.id = 1234
        instance = Mock(field1=subinstance)
        data_combiner = DataCombiner(instance, None)
        assert data_combiner.get_value_id('field1') == str(subinstance.id)

    def test_get_value_id_value(self):
        """Tests getting a foreign key from update data."""
        subinstance = Mock()
        subinstance.id = 1234
        new_subinstance = Mock()
        new_subinstance.id = 456
        instance = Mock(field1=subinstance)
        data_combiner = DataCombiner(instance, {'field1': new_subinstance})
        assert data_combiner.get_value_id('field1') == str(new_subinstance.id)

    def test_get_value_auto_instance(self, monkeypatch):
        """Tests that get_value_auto() returns the ID for a foreign key."""
        subinstance = Mock()
        subinstance.id = 1234
        instance = Mock(field1=subinstance)
        model = Mock()
        mock_field_info = Mock(
            relations={'field1': Mock(to_many=False)}
        )
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert data_combiner.get_value_auto('field1') == str(subinstance.id)
        assert data_combiner['field1'] == str(subinstance.id)

    def test_get_value_auto_to_many(self, monkeypatch):
        """Tests that get_value_auto() returns a list-like object for a to-many field."""
        instance = Mock(field1=MagicMock())
        instance.field1.all.return_value = [123]
        model = Mock()
        mock_field_info = Mock(
            relations={'field1': Mock(to_many=True)}
        )
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert data_combiner.get_value_auto('field1') == [123]
        assert data_combiner['field1'] == [123]

    def test_get_value_auto_normal_field(self, monkeypatch):
        """Tests that get_value_auto() returns value for a normal field."""
        instance = Mock(field1=123)
        model = Mock()
        mock_field_info = Mock(relations={})
        monkeypatch.setattr(
            validate_utils, '_get_model_field_info', Mock(return_value=mock_field_info)
        )
        data_combiner = DataCombiner(instance, None, model=model)
        assert data_combiner.get_value_auto('field1') == 123
        assert data_combiner['field1'] == 123
