from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import (
    AndRule,
    ConditionalRule,
    EqualsRule,
    FieldAndError,
    InRule,
    IsFieldBeingUpdatedAndIsNotBlankRule,
    IsFieldBeingUpdatedRule,
    IsFieldRule,
    OperatorRule,
    RequiredUnlessAlreadyBlankValidator,
    RulesBasedValidator,
    ValidationRule,
)


@pytest.mark.parametrize(
    'data,field,op,res',
    (
        ({'colour': 'red'}, 'colour', lambda val: val == 'red', True),
        ({'colour': 'red'}, 'colour', lambda val: val == 'blue', False),
    ),
)
def test_operator_rule(data, field, op, res):
    """Tests ValidationCondition for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = OperatorRule(field, op)
    assert condition(combiner) == res


@pytest.mark.parametrize(
    'data,field,test_value,res',
    (
        ({'colour': 'red'}, 'colour', 'red', True),
        ({'colour': 'red'}, 'colour', 'blue', False),
    ),
)
def test_equals_rule(data, field, test_value, res):
    """Tests ValidationCondition for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = EqualsRule(field, test_value)
    assert condition(combiner) == res


@pytest.mark.parametrize(
    'data,instance,expected_result',
    (
        ({}, Mock(my_date=None), False),
        ({'my_date': 1}, Mock(my_date=None), True),
        ({'my_date': None}, Mock(my_date=None), False),
        ({'my_date': 1}, Mock(my_date=1), False),
    ),
)
def test_is_field_being_updated_rule(data, instance, expected_result):
    """Tests IsFieldBeingUpdatedRule for various cases."""
    combiner = Mock(data=data, instance=instance)
    condition = IsFieldBeingUpdatedRule('my_date')
    assert condition(combiner) == expected_result


@pytest.mark.parametrize(
    'data,expected_result',
    (
        ({}, False),
        ({'my_date': 1}, True),
        ({'my_date': None}, False),
    ),
)
def test_is_field_being_updated_and_is_not_blank_rule(data, expected_result):
    """Tests IsFieldBeingUpdatedRuleAndIsNotBlankRule for various cases."""
    combiner = Mock(data=data)
    condition = IsFieldBeingUpdatedAndIsNotBlankRule('my_date')
    assert condition(combiner) == expected_result


@pytest.mark.parametrize(
    'data,field,expected_result',
    (
        ({}, 'my_date', False),
        ({'my_date': 1}, 'my_date', True),
        ({'my_date': None}, 'my_date', False),
    ),
)
@freeze_time('2019-05-01')
def test_is_field_rule(data, field, expected_result):
    """Tests IsFieldRule for various cases."""
    combiner = Mock(data=data)
    condition = IsFieldRule(field, lambda x: x == 1)
    assert condition(combiner) == expected_result


@pytest.mark.parametrize(
    'data,field,test_value,res',
    (
        ({'colour': 'red'}, 'colour', ['red', 'green'], True),
        ({'colour': 'red'}, 'colour', ['blue', 'green'], False),
    ),
)
def test_in_rule(data, field, test_value, res):
    """Tests InRule for various cases."""
    combiner = Mock(spec_set=DataCombiner, __getitem__=lambda self, field_: data[field_])
    condition = InRule(field, test_value)
    assert condition(combiner) == res


@pytest.mark.parametrize(
    'rule_res,when_res,res',
    (
        (True, True, True),
        (False, True, False),
        (True, False, True),
        (False, False, True),
    ),
)
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


@pytest.mark.parametrize('subrule1_res', (True, False))
@pytest.mark.parametrize('subrule2_res', (True, False))
def test_and_rule_combines_other_rules(subrule1_res, subrule2_res):
    """Test that AndRule combines sub-rules using the AND operator."""
    rule = AndRule(
        _make_stub_rule('field1', subrule1_res),
        _make_stub_rule('field2', subrule2_res),
    )
    combiner = Mock(spec_set=DataCombiner)
    assert rule(combiner) == (subrule1_res and subrule2_res)


@pytest.mark.parametrize(
    'rules,when,res',
    (
        (
            (_make_stub_rule('field1', False),),
            _make_stub_rule('field_when', True),
            [FieldAndError('field1', 'error')],
        ),
        (
            (_make_stub_rule('field1', False), _make_stub_rule('field2', False)),
            _make_stub_rule('field_when', True),
            [FieldAndError('field1', 'error'), FieldAndError('field2', 'error')],
        ),
        (
            (_make_stub_rule('field1', True), _make_stub_rule('field2', False)),
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
        (
            (_make_stub_rule(None, False),),
            _make_stub_rule('field_when', True),
            [FieldAndError('non_field_errors', 'error')],
        ),
    ),
)
def test_validation_rule(rules, when, res):
    """Tests ValidationRule for various cases."""
    combiner = Mock(spec_set=DataCombiner)
    rule = ValidationRule('error', *rules, when=when)
    assert rule(combiner) == res


def _make_stub_validation_rule(errors=None):
    return Mock(return_value=errors)


class TestRulesBasedValidator:
    """RulesBasedValidator tests."""

    @pytest.mark.parametrize(
        'rules',
        (
            (_make_stub_validation_rule([]),),
            (_make_stub_validation_rule([]), _make_stub_validation_rule([])),
        ),
    )
    def test_validation_passes(self, rules):
        """Test that validation passes when the rules pass."""
        instance = Mock()
        serializer = Mock(instance=instance, error_messages={'error': 'test error'})
        validator = RulesBasedValidator(*rules)
        assert validator({}, serializer) is None

    @pytest.mark.parametrize(
        'rules,errors',
        (
            (
                (
                    _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                ),
                {'field1': ['test error']},
            ),
            (
                (
                    _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                    _make_stub_validation_rule([FieldAndError('field2', 'error')]),
                ),
                {'field1': ['test error'], 'field2': ['test error']},
            ),
            (
                (
                    _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                    _make_stub_validation_rule([]),
                ),
                {'field1': ['test error']},
            ),
            (
                (
                    _make_stub_validation_rule([FieldAndError('field1', 'error')]),
                    _make_stub_validation_rule([FieldAndError('field1', 'error2')]),
                ),
                {'field1': ['test error', 'test error 2']},
            ),
        ),
    )
    def test_validation_fails(self, rules, errors):
        """Test that validation fails when any rule fails."""
        instance = Mock()
        serializer = Mock(
            instance=instance, error_messages={
                'error': 'test error',
                'error2': 'test error 2',
            },
        )
        validator = RulesBasedValidator(*rules)

        with pytest.raises(ValidationError) as excinfo:
            validator({}, serializer)
        assert excinfo.value.detail == errors


class TestRequiredUnlessAlreadyBlankValidator:
    """RequiredUnlessAlreadyBlank tests."""

    @pytest.mark.parametrize(
        'create_data,update_data,partial,should_raise',
        (
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
        ),
    )
    def test_update(self, create_data, update_data, partial, should_raise):
        """Tests validation during updates."""
        instance = Mock(**create_data)
        serializer = Mock(instance=instance, partial=partial)
        validator = RequiredUnlessAlreadyBlankValidator('field1')

        if should_raise:
            with pytest.raises(ValidationError) as excinfo:
                validator(update_data, serializer)
            assert excinfo.value.detail['field1'] == validator.required_message
        else:
            validator(update_data, serializer)

    @pytest.mark.parametrize(
        'create_data,should_raise',
        (
            ({}, True),
            ({'field1': None}, True),
            ({'field1': 'blah'}, False),
        ),
    )
    def test_create(self, create_data, should_raise):
        """Tests validation during instance creation."""
        serializer = Mock(instance=None, partial=False)
        validator = RequiredUnlessAlreadyBlankValidator('field1')

        if should_raise:
            with pytest.raises(ValidationError) as excinfo:
                validator(create_data, serializer)
            assert excinfo.value.detail['field1'] == validator.required_message
        else:
            validator(create_data, serializer)
