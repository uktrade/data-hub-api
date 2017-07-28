from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import AnyOfValidator, DataCombiner


def test_any_of_none():
    """Tests that validation fails if no any-of fields provided."""
    instance = SimpleNamespace(field_a=None, field_b=None)
    validator = AnyOfValidator('field_a', 'field_b')
    validator.set_context(Mock(instance=instance))
    with pytest.raises(ValidationError):
        validator({})


def test_any_of_some():
    """Tests that validation passes if some any-of fields provided."""
    instance = SimpleNamespace(field_a=None, field_b=None)
    validator = AnyOfValidator('field_a', 'field_b')
    validator.set_context(Mock(instance=instance))
    validator({'field_a': Mock()})


def test_any_of_all():
    """Tests that validation passes if all any-of fields provided."""
    instance = SimpleNamespace(field_a=None, field_b=None)
    validator = AnyOfValidator('field_a', 'field_b')
    validator.set_context(Mock(instance=instance))
    validator({'field_a': Mock(), 'field_b': Mock()})


class TestDataCombiner:
    """Data Combiner tests."""

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
