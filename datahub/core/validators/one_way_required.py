from rest_framework import serializers

from datahub.core.validate_utils import is_blank


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
