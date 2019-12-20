from rest_framework import serializers

from datahub.core.validate_utils import is_blank


class RequiredUnlessAlreadyBlankValidator:
    """
    Class-level DRF validator for required fields that are allowed to stay null if already
    null.

    (Because of how validation works in DRF, this cannot be done as a field-level validator.)
    """

    requires_context = True
    required_message = 'This field is required.'

    def __init__(self, *fields):
        """
        Initialises the validator with a list of fields to individually validate.

        :param fields:  Fields that should be required (when not already null)
        """
        self.fields = fields

    def __call__(self, attrs, serializer):
        """Performs validation (called by DRF)."""
        instance = serializer.instance
        is_partial = serializer.partial

        errors = {}
        for field in self.fields:
            if instance and is_blank(getattr(instance, field)):
                continue

            if is_partial and field not in attrs:
                continue

            if is_blank(attrs.get(field)):
                errors[field] = self.required_message

        if errors:
            raise serializers.ValidationError(errors)

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}(*{self.fields!r})'
