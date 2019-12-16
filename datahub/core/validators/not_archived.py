from rest_framework import serializers


class NotArchivedValidator:
    """Class-level DRF validator that checks that the object has not been archived."""

    requires_context = True
    archived_message = 'This record has been {has_been_word} and cannot be edited.'

    def __init__(self, archived_field='archived', error_has_been_word='archived'):
        """
        Initialises the validator with the field to use to check if the object has been archived,
        and the past participle of the verb to use in the error message to describe what
        happened to the object (e.g. archived, deactivated).

        This validator only has an effect on updates.
        """
        self.archived_field = archived_field
        self.error_has_been_word = error_has_been_word

    def __call__(self, attrs, serializer):
        """
        Performs validation (called by DRF).

        We don't use DataCombiner here (and only look at the archived status on the model
        instance) as the archived status is changed via separate endpoints (and is read-only in
        the main update endpoints).
        """
        instance = serializer.instance
        if instance and getattr(instance, self.archived_field):
            error_message = self.archived_message.format(has_been_word=self.error_has_been_word)
            raise serializers.ValidationError(detail=error_message, code='archived')

    def __repr__(self):
        """Returns the string representation of this object."""
        return (
            f'{self.__class__.__name__}('
            f'archived_field={self.archived_field!r}, '
            f'error_has_been_word={self.error_has_been_word!r}'
            f')'
        )
