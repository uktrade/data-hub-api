from abc import ABC, abstractmethod
from functools import partial
from operator import eq
from typing import Any, Callable

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank


class AnyOfValidator:
    """
    Any-of validator for DRF serializer classes.

    Checks that at least one of the specified fields has a value that is
    not None.

    To be used at class-level only. For updates, values from the model
    instance are used where the fields are not part of the update request.
    """

    message = 'One or more of {field_names} must be provided.'

    def __init__(self, *fields, message=None):
        """
        Initialises the validator.

        :param fields:  Fields to perform any-of validation on
        :param message: Optional custom error message
        """
        self.fields = fields
        self.message = message or self.message
        self.serializer = None

    def set_context(self, serializer):
        """
        Saves a reference to the serializer object.

        Called by DRF.
        """
        self.serializer = serializer

    def __call__(self, attrs):
        """
        Performs validation. Called by DRF.

        :param attrs:   Serializer data (post-field-validation/processing)
        """
        data_combiner = DataCombiner(self.serializer.instance, attrs)
        values = (data_combiner.get_value(field) for field in self.fields)
        value_present = any(value for value in values if value is not None)
        if not value_present:
            field_names = ', '.join(self.fields)
            message = self.message.format(field_names=field_names)
            raise ValidationError(message, code='any_of')

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}(fields={self.fields!r})'


class RequiredUnlessAlreadyBlankValidator:
    """
    Class-level DRF validator for required fields that are allowed to stay null if already
    null.

    (Because of how validation works in DRF, this cannot be done as a field-level validator.)
    """

    required_message = 'This field is required.'

    def __init__(self, *fields):
        """
        Initialises the validator with a list of fields to individually validate.

        :param fields:  Fields that should be required (when not already null)
        """
        self.fields = fields
        self.instance = None
        self.partial = None

    def __call__(self, attrs):
        """Performs validation (called by DRF)."""
        errors = {}
        for field in self.fields:
            if self.instance and is_blank(getattr(self.instance, field)):
                continue

            if self.partial and field not in attrs:
                continue

            if is_blank(attrs.get(field)):
                errors[field] = self.required_message

        if errors:
            raise serializers.ValidationError(errors)

    def set_context(self, serializer):
        """
        Saves a reference to the model instance and whether this is a partial update.

        Called by DRF.
        """
        self.instance = serializer.instance
        self.partial = serializer.partial

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}(*{self.fields!r})'


class AddressValidator:
    """Validator for addresses."""

    message = 'This field is required.'

    DEFAULT_FIELDS_MAPPING = {
        'address_1': {'required': True},
        'address_2': {'required': False},
        'address_town': {'required': True},
        'address_county': {'required': False},
        'address_postcode': {'required': False},
        'address_country': {'required': True},
    }

    def __init__(self, lazy=False, fields_mapping=None):
        """
        Init the params.

        :param lazy: True if you want to skip validation when none of the fields are set.
            Useful when validating an extra and optional address where some fields
            become required only if any of the fields are set.
        :fields_mapping: dict with the field as a key and the value as a dict with
            `required` == True or False
        """
        self.lazy = lazy
        if fields_mapping:
            self.fields_mapping = fields_mapping
        else:
            self.fields_mapping = self.DEFAULT_FIELDS_MAPPING
        self.instance = None

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer, 'instance', None)

    def _should_validate(self, data_combined):
        """
        :returns: True if the data should be validated.
            If lazy == True, the data should always be validated
            If lazy == False, validate only if at least one field is set
        """
        if not self.lazy:
            return True
        return any(data_combined.values())

    def _validate_fields(self, data_combined):
        """
        :returns: a dict containing potential errors
        """
        errors = {}
        for field_name, mapping in self.fields_mapping.items():
            if not mapping['required']:
                continue
            if not data_combined.get(field_name):
                errors[field_name] = [self.message]
        return errors

    def __call__(self, data):
        """Validate the address fields."""
        data_combiner = DataCombiner(self.instance, data)

        data_combined = {
            field_name: data_combiner.get_value(field_name)
            for field_name in self.fields_mapping.keys()
        }

        if not self._should_validate(data_combined):
            return

        errors = self._validate_fields(data_combined)
        if errors:
            raise ValidationError(errors)


class AbstractRule(ABC):
    """Abstract base class for rules."""

    @property
    @abstractmethod
    def field(self) -> str:
        """Field the rule applies to."""

    @abstractmethod
    def __call__(self, combiner) -> bool:
        """Evaluates the rule."""


class BaseRule(AbstractRule):
    """Base class for rules."""

    def __init__(self, field: str=None):
        """Sets the field name."""
        self._field = field

    @property
    def field(self):
        """Field the rule applies to."""
        return self._field


class OperatorRule(BaseRule):
    """Simple operator-based rule for a field."""

    def __init__(self,
                 field: str,
                 operator_: Callable):
        """
        Initialises the rule.

        :param field:     The name of the field the rule applies to.
        :param operator_: Callable that returns a truthy or falsey value (indicating whether the
                          value is valid). Will be called with the field value as the first
                          argument.
        """
        super().__init__(field)
        self._operator = operator_

    def __call__(self, combiner) -> bool:
        """Test whether the rule passes or fails."""
        value = combiner[self.field]
        return self._operator(value)


class EqualsRule(OperatorRule):
    """Equals operator-based rule for a field."""

    def __init__(self, field: str, value: Any):
        """
        Initialises the rule.

        :param field: The name of the field the rule applies to.
        :param value: Value to test equality with.
        """
        super().__init__(field, partial(eq, value))


class ConditionalRule:
    """A rule that is only checked when a condition is met."""

    def __init__(self, rule: AbstractRule, when: AbstractRule=None):
        """
        Initialises the rule.

        :param rule: Rule that must pass.
        :param when: Optional conditional rule to check before applying this rule.
                     If the condition evaluates to False, validation passes.
        """
        self._rule = rule
        self._condition = when

    @property
    def field(self):
        """The field that is being validated."""
        return self._rule.field

    def __call__(self, combiner) -> bool:
        """Test whether the rule passes or fails."""
        if self._condition and not self._condition(combiner):
            return True

        return self._rule(combiner)

    def __repr__(self):
        """Returns the Python representation of this object."""
        return (
            f'{self.__class__.__name__}({self._rule!r}, when={self._condition!r})'
        )


class AllIsBlankRule(BaseRule):
    """A rule that checks if all fields in a list are blank."""

    def __init__(self, *fields):
        """
        Initialises the rule.

        :param fields: Fields to check for blankness.
        """
        super().__init__()
        self._fields = fields

    def __call__(self, combiner) -> bool:
        """Test whether all of the fields are blank."""
        return all(is_blank(combiner[field]) for field in self._fields)


class AnyIsNotBlankRule(BaseRule):
    """A rule that checks if any of a list of specified fields is not blank."""

    def __init__(self, *fields: str):
        """
        Initialises the rule.

        :param fields: Fields to check for non-blankness.
        """
        super().__init__()
        self._fields = fields

    def __call__(self, combiner) -> bool:
        """Test whether any of the fields are not blank."""
        return any(is_not_blank(combiner[field]) for field in self._fields)


class ValidationRule(ConditionalRule):
    """A rule that is only checked when a condition is met."""

    def __init__(self,
                 error_key: str,
                 rule: OperatorRule,
                 when: OperatorRule=None):
        """
        Initialises a validation rule.

        :param error_key: The key of the error message associated with this rule.
        :param rule:      Rule that must pass.
        :param when:      Optional conditional rule to check before applying this rule.
                          If the condition evaluates to False, validation passes.
        """
        super().__init__(rule, when=when)
        self.error_key = error_key

    def __repr__(self):
        """Returns the Python representation of this object."""
        return (
            f'{self.__class__.__name__}({self.error_key!r}, {self._rule!r}, '
            f'when={self._condition!r})'
        )


class RulesBasedValidator:
    """
    Class-level DRF validator for cross-field validation.

    Validation is performed using rules (instances of ValidationRule).
    """

    def __init__(self, *rules: ValidationRule):
        """
        Initialises the validator with rules.
        """
        self._rules = rules
        self._serializer = None

    def __call__(self, data):
        """
        Performs validation.

        Called by DRF.
        """
        errors = {}
        combiner = DataCombiner(
            instance=self._serializer.instance,
            update_data=data,
            serializer=self._serializer,
            model=self._serializer.Meta.model,
        )
        for rule in self._rules:
            if not rule(combiner):
                fields_errors = errors.setdefault(rule.field, [])
                fields_errors.append(self._serializer.error_messages[rule.error_key])

        if errors:
            raise serializers.ValidationError(errors)

    def set_context(self, serializer):
        """
        Saves a reference to the serializer instance.

        Called by DRF.
        """
        self._serializer = serializer

    def __repr__(self):
        """Returns the Python representation of this object."""
        return f'{self.__class__.__name__}(*{self._rules!r})'
