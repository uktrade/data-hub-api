from abc import ABC, abstractmethod
from collections import namedtuple
from functools import partial
from operator import contains, eq
from typing import Any, Callable, Iterable, Sequence

from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank


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

    def __init__(self, field: str = None):
        """Sets the field name."""
        self._field = field

    @property
    def field(self):
        """Field the rule applies to."""
        return self._field


class OperatorRule(BaseRule):
    """Simple operator-based rule for a field."""

    def __init__(
        self,
        field: str,
        operator_: Callable,
    ):
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


class InRule(OperatorRule):
    """Contains operator-based rule for a field. Checks that field value is in values"""

    def __init__(self, field: str, value: Iterable[Any]):
        """
        Initialises the rule.

        :param field: The name of the field the rule applies to.
        :param value: a list of Values to test equality with.
        """
        super().__init__(field, partial(contains, value))


class ConditionalRule:
    """A rule that is only checked when a condition is met."""

    def __init__(self, rule: AbstractRule, when: AbstractRule = None):
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


class AndRule(BaseRule):
    """
    Field-less AND rule that can be used to combine other rules in the `when` argument in
    `ValidationRule.__init__`.

    (It's not intended to be used with the `rules` argument in `ValidationRule.__init__`,
    as multiple rules can simply be provided instead.)
    """

    def __init__(self, *rules: AbstractRule):
        """
        Initialise the rule.

        :param rules: Sub-rules to combine using the AND operator.
        """
        super().__init__()
        self._rules = rules

    def __call__(self, combiner) -> bool:
        """Test whether all of the sub-rules pass."""
        return all(rule(combiner) for rule in self._rules)


FieldAndError = namedtuple('FieldAndError', ('field', 'error_key'))


class AbstractValidationRule(ABC):
    """Abstract base class for RulesBasedValidator validation rules."""

    @abstractmethod
    def __call__(self, combiner) -> Sequence[FieldAndError]:
        """Performs validation, returning a list of errors."""


class ValidationRule(AbstractValidationRule):
    """
    A simple validation rule, taking a list of rules that must be met if a condition is also met.

    Used with RulesBasedValidator.
    """

    def __init__(
        self,
        error_key: str,
        *rules: AbstractRule,
        when: AbstractRule = None,
    ):
        """
        Initialises a validation rule.

        :param error_key: The key of the error message associated with this rule.
        :param rule:      Rule that must pass.
        :param when:      Optional conditional rule to check before applying this rule.
                          If the condition evaluates to False, validation passes.
        """
        self._rules = [ConditionalRule(rule, when=when) for rule in rules]
        self._error_key = error_key

    def __call__(self, combiner) -> Sequence[FieldAndError]:
        """Performs validation, returning a list of errors."""
        errors = []
        for rule in self._rules:
            if not rule(combiner):
                error = FieldAndError(
                    rule.field or api_settings.NON_FIELD_ERRORS_KEY,
                    self._error_key,
                )
                errors.append(error)
        return errors

    def __repr__(self):
        """Returns the Python representation of this object."""
        return f'{self.__class__.__name__}({self._error_key!r}, {self._rules!r})'


class RulesBasedValidator:
    """
    Class-level DRF validator for cross-field validation.

    Validation is performed using rules (instances of AbstractValidationRule).
    """

    def __init__(self, *rules: AbstractValidationRule):
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
            rule_errors = rule(combiner)
            for error in rule_errors:
                fields_errors = errors.setdefault(error.field, [])
                fields_errors.append(self._serializer.error_messages[error.error_key])

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
