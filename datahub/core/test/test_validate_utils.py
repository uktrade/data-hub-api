from operator import eq
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import (
    AnyOfValidator, Condition, DataCombiner, is_blank, RequiredUnlessAlreadyBlank,
    RulesBasedValidator, ValidationRule
)


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


@pytest.mark.parametrize('data,field,op,args,res', (
    ({'colour': 'red'}, 'colour', eq, ('red',), True),
    ({'colour': 'red'}, 'colour', eq, ('blue',), False),
))
def test_validation_condition(data, field, op, args, res):
    """Tests ValidationCondition for various cases."""
    combiner = Mock(spec_set=DataCombiner, get_value=lambda field_: data[field_])
    condition = Condition(field, op, args)
    assert condition(combiner) == res


@pytest.mark.parametrize('data,field,op,condition,res', (
    ({'colour': 'red', 'valid': True}, 'valid', bool, lambda x: True, True),
    ({'colour': 'red', 'valid': False}, 'valid', bool, lambda x: True, False),
    ({'colour': 'red', 'valid': True}, 'valid', bool, lambda x: False, True),
    ({'colour': 'red', 'valid': False}, 'valid', bool, lambda x: False, True),
))
def test_validation_rule(data, field, op, condition, res):
    """Tests ValidationRule for various cases."""
    combiner = Mock(spec_set=DataCombiner, get_value=lambda field_: data[field_])
    rule = ValidationRule('error_key', field, op, condition=condition)
    assert rule(combiner) == res


def _make_stub_rule(field, return_value):
    return Mock(return_value=return_value, error_key='error', rule=Mock(field=field))


class TestRulesBasedValidator:
    """RulesBasedValidator tests."""

    @pytest.mark.parametrize('rules', (
        (_make_stub_rule('field1', True),),
        (_make_stub_rule('field1', True), _make_stub_rule(True, 'field2')),
    ))
    def test_validation_passes(self, rules):
        """Test that validation passes when the rules pass."""
        instance = Mock()
        serializer = Mock(instance=instance, error_messages={'error': 'test error'})
        validator = RulesBasedValidator(*rules)
        validator.set_context(serializer)
        assert validator({}) is None

    @pytest.mark.parametrize('rules,errors', (
        (
            (_make_stub_rule('field1', False),),
            {'field1': 'test error'}
        ),
        (
            (_make_stub_rule('field1', False), _make_stub_rule('field2', False),),
            {'field1': 'test error', 'field2': 'test error'}
        ),
        (
            (_make_stub_rule('field1', False), _make_stub_rule('field2', True),),
            {'field1': 'test error'}
        ),
    ))
    def test_validation_fails(self, rules, errors):
        """Test that validation fails when any rule fails."""
        instance = Mock()
        serializer = Mock(instance=instance, error_messages={'error': 'test error'})
        validator = RulesBasedValidator(*rules)
        validator.set_context(serializer)
        with pytest.raises(ValidationError) as excinfo:
            validator({})
        assert excinfo.value.detail == errors


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


class TestRequiredUnlessAlreadyBlank:
    """RequiredUnlessAlreadyBlank tests."""

    @pytest.mark.parametrize('create_data,update_data,partial,should_raise', (
        ({'field1': None}, {'field1': None}, False, False),
        ({'field1': None}, {'field1': None}, True, False),
        ({'field1': None}, {'field1': 'blah'}, False, False),
        ({'field1': None}, {'field1': 'blah'}, True, False),
        ({'field1': None}, {}, False, False),
        ({'field1': None}, {}, True, False),
        ({'field1': 'blah'}, {'field1': None}, False, True),
        ({'field1': 'blah'}, {'field1': None}, True, True),
        ({'field1': 'blah'}, {'field1': 'blah'}, False, False),
        ({'field1': 'blah'}, {'field1': 'blah'}, True, False),
        ({'field1': 'blah'}, {}, False, True),
        ({'field1': 'blah'}, {}, True, False),
    ))
    def test_update(self, create_data, update_data, partial, should_raise):
        """Tests validation during updates."""
        instance = Mock(**create_data)
        serializer = Mock(instance=instance, partial=partial)
        validator = RequiredUnlessAlreadyBlank('field1')
        validator.set_context(serializer)
        if should_raise:
            with pytest.raises(ValidationError) as excinfo:
                validator(update_data)
            assert excinfo.value.detail['field1'] == validator.required_message
        else:
            validator(update_data)

    @pytest.mark.parametrize('create_data,should_raise', (
        ({}, True),
        ({'field1': None}, True),
        ({'field1': 'blah'}, False),
    ))
    def test_create(self, create_data, should_raise):
        """Tests validation during instance creation."""
        serializer = Mock(instance=None, partial=False)
        validator = RequiredUnlessAlreadyBlank('field1')
        validator.set_context(serializer)
        if should_raise:
            with pytest.raises(ValidationError) as excinfo:
                validator(create_data)
            assert excinfo.value.detail['field1'] == validator.required_message
        else:
            validator(create_data)
