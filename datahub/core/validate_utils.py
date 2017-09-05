from collections.abc import Sequence

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


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


class RequiredUnlessAlreadyBlank:
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


class DataCombiner:
    """
    Combines values from the dict of updated data and the model instance fields.
    Its methods return the first value found in the chain (update_data, instance).

    Used for cross-field validation of v3 endpoints (because PATCH requests
    will only contain data for fields being updated).
    """

    def __init__(self, instance, update_data):
        """Initialises the combiner."""
        if instance is None and update_data is None:
            raise TypeError('One of instance and update_data must be provided '
                            'and not None')

        if update_data is None:
            update_data = {}

        self.instance = instance
        self.data = update_data

    def get_value(self, field_name):
        """Returns the value of a standard field."""
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name)
        return None

    def get_value_to_many(self, field_name):
        """Returns an object representing to-many field values."""
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name).all()
        return ()

    def get_value_id(self, field_name):
        """Returns the ID of foreign keys."""
        value = self.get_value(field_name)
        return str(value.id) if value else None


def is_blank(value):
    """Returns True if a value is considered empty or blank."""
    return value in (None, '') or (isinstance(value, Sequence) and len(value) == 0)
