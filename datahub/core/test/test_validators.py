from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import (
    AddressValidator,
    AnyOfValidator,
    ConditionalRule,
    EqualsRule,
    FieldAndError,
    InRule,
    OperatorRule,
    RequiredUnlessAlreadyBlankValidator,
    RulesBasedValidator,
    ValidationRule,
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


class TestAddressValidator:
    """Tests for the AddressValidator."""

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('with_instance', (True, False))
    def test_fails_without_any_fields_if_not_lazy(self, values_as_data, with_instance):
        """
        Test that the validation fails if lazy == False and the required fields
        are not specified.

        Test all scenarios:
        - with non-set fields on the instance and empty data
        - with non-set fields in the data param
        - with instance == None and empty data
        - with instance == None and non-set fields in the data param
        """
        address_fields = {
            'address1': None,
            'address2': None,
            'town': None,
        }

        instance = mock.Mock(**address_fields) if with_instance else None
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=False,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            }
        )

        validator.set_context(mock.Mock(instance=instance))

        with pytest.raises(ValidationError) as exc:
            validator(data)
        assert exc.value.detail == {
            'address1': ['This field is required.'],
            'town': ['This field is required.']
        }

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('with_instance', (True, False))
    def test_passes_without_any_fields_set_if_lazy(self, values_as_data, with_instance):
        """
        Test that the validation passes if lazy == True and none of the fields
        are specified.

        Test all scenarios:
        - with non-set fields on the instance and empty data
        - with non-set fields in the data param
        - with instance == None and empty data
        - with instance == None and non-set fields in the data param
        """
        address_fields = {
            'address1': None,
            'address2': None,
            'town': None,
        }

        instance = mock.Mock(**address_fields) if with_instance else None
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=True,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            }
        )

        validator.set_context(mock.Mock(instance=instance))

        try:
            validator(data)
        except Exception:
            pytest.fail('Should not raise a validator error.')

    @pytest.mark.parametrize('values_as_data', (True, False))
    @pytest.mark.parametrize('lazy', (True, False))
    def test_fails_without_all_required_fields_set(self, values_as_data, lazy):
        """
        Test that the validation fails if only some fields are set but not
        all the required ones are.

        Test all scenarios:
        - with lazy == True and empty data
        - with lazy == True and only some fields set in data
        - with lazy == False and empty data
        - with lazy == False and only some fields set in data
        """
        address_fields = {
            'address1': None,
            'address2': 'lorem ipsum',
            'town': None,
        }

        instance = mock.Mock(**address_fields)
        data = address_fields if values_as_data else {}

        validator = AddressValidator(
            lazy=lazy,
            fields_mapping={
                'address1': {'required': True},
                'address2': {'required': False},
                'town': {'required': True},
            }
        )

        validator.set_context(mock.Mock(instance=instance))

        with pytest.raises(ValidationError) as exc:
            validator(data)
        assert exc.value.detail == {
            'address1': ['This field is required.'],
            'town': ['This field is required.']
        }

    def test_defaults(self):
        """Test the defaults props."""
        validator = AddressValidator()
        assert not validator.lazy
        assert validator.fields_mapping == validator.DEFAULT_FIELDS_MAPPING


@pytest.mark.parametrize('data,field,op,res', (
    ({'colour': 'red'}, 'colour', lambda val: val == 'red', True),
    ({'colour': 'red'}, 'colour', lambda val: val == 'blue', False),
))
def test_operator_rule(data, field, op, res):
    """Tests ValidationCondition for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = OperatorRule(field, op)
    assert condition(combiner) == res


@pytest.mark.parametrize('data,field,test_value,res', (
    ({'colour': 'red'}, 'colour', 'red', True),
    ({'colour': 'red'}, 'colour', 'blue', False),
))
def test_equals_rule(data, field, test_value, res):
    """Tests ValidationCondition for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = EqualsRule(field, test_value)
    assert condition(combiner) == res


@pytest.mark.parametrize('data,field,test_value,res', (
    ({'colour': 'red'}, 'colour', ['red', 'green'], True),
    ({'colour': 'red'}, 'colour', ['blue', 'green'], False),
))
def test_in_rule(data, field, test_value, res):
    """Tests InRule for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = InRule(field, test_value)
    assert condition(combiner) == res


@pytest.mark.parametrize('rule_res,when_res,res', (
    (True, True, True),
    (False, True, False),
    (True, False, True),
    (False, False, True),
))
def test_conditional_rule(rule_res, when_res, res):
    """Tests ConditionalRule for various cases."""
    combiner = Mock(spec_set=DataCombiner)
    rule = Mock(spec_set=OperatorRule)
    rule.return_value = rule_res
    condition = Mock(spec=OperatorRule)
    condition.return_value = when_res
    rule = ConditionalRule(rule, when=condition)
    assert rule(combiner) == res


def _make_stub_rule(field, is_valid):
    return Mock(return_value=is_valid, field=field)


@pytest.mark.parametrize('rules,when,res', (
    (
        (_make_stub_rule('field1', False),),
        _make_stub_rule('field_when', True),
        [FieldAndError('field1', 'error')],
    ),
    (
        (_make_stub_rule('field1', False), _make_stub_rule('field2', False),),
        _make_stub_rule('field_when', True),
        [FieldAndError('field1', 'error'), FieldAndError('field2', 'error')],
    ),
    (
        (_make_stub_rule('field1', True), _make_stub_rule('field2', False),),
        _make_stub_rule('field_when', True),
        [FieldAndError('field2', 'error')],
    ),
    (
        (_make_stub_rule('field1', True),),
        _make_stub_rule('field_when', False),
        [],
    ),
    (
        (_make_stub_rule('field1', False),),
        _make_stub_rule('field_when', False),
        [],
    ),
))
def test_validation_rule(rules, when, res):
    """Tests ValidationRule for various cases."""
    combiner = Mock(spec_set=DataCombiner)
    rule = ValidationRule('error', *rules, when=when)
    assert rule(combiner) == res


def _make_stub_validation_rule(errors=None):
    return Mock(return_value=errors)


class TestRulesBasedValidator:
    """RulesBasedValidator tests."""

    @pytest.mark.parametrize('rules', (
        (_make_stub_validation_rule([]),),
        (_make_stub_validation_rule([]), _make_stub_validation_rule([])),
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
            (
                _make_stub_validation_rule([FieldAndError('field1', 'error')]),
            ),
            {'field1': ['test error']}
        ),
        (
            (
                _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                _make_stub_validation_rule([FieldAndError('field2', 'error')]),
            ),
            {'field1': ['test error'], 'field2': ['test error']}
        ),
        (
            (
                _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                _make_stub_validation_rule([]),
            ),
            {'field1': ['test error']}
        ),
        (
            (
                _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                _make_stub_validation_rule([FieldAndError('field1', 'error2')]),
            ),
            {'field1': ['test error', 'test error 2']}
        ),
    ))
    def test_validation_fails(self, rules, errors):
        """Test that validation fails when any rule fails."""
        instance = Mock()
        serializer = Mock(instance=instance, error_messages={
            'error': 'test error',
            'error2': 'test error 2',
        })
        validator = RulesBasedValidator(*rules)
        validator.set_context(serializer)
        with pytest.raises(ValidationError) as excinfo:
            validator({})
        assert excinfo.value.detail == errors


class TestRequiredUnlessAlreadyBlankValidator:
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
        validator = RequiredUnlessAlreadyBlankValidator('field1')
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
        validator = RequiredUnlessAlreadyBlankValidator('field1')
        validator.set_context(serializer)
        if should_raise:
            with pytest.raises(ValidationError) as excinfo:
                validator(create_data)
            assert excinfo.value.detail['field1'] == validator.required_message
        else:
            validator(create_data)
