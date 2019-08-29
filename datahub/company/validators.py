import re

from rest_framework.exceptions import ValidationError

_INVALID_COMPANY_NUMBER_RE = re.compile(r'[^A-Z0-9]')


class NotATransferredCompanyValidator:
    """Validates that a company has not been marked as a duplicate."""

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def __call__(self, data):
        """Performs validation."""
        if self.instance.transferred_to:
            transfer_reason = self.instance.get_transfer_reason_display()
            raise ValidationError(
                f'This record is no longer in use and its data has been transferred to another '
                f'record for the following reason: {transfer_reason}.',
                'transferred_company',
            )


class ArchiveReasonRestrictedValidator:
    """
    Validates that an archived company does not have an archive reason which
    restricts unarchiving it.
    """

    RESTRICTED_REASONS = (
        'Not a valid company',
    )

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def __call__(self, data):
        """Performs validation."""
        if self.instance.archived_reason in self.RESTRICTED_REASONS:
            raise ValidationError(
                'Records that have been archived with the reason '
                f'"{self.instance.archived_reason}" cannot be unarchived.',
            )


def has_uk_establishment_number_prefix(value):
    """Checks if a UK establishment number has the correct (BR) prefix."""
    return not value or value.startswith('BR')


def has_no_invalid_company_number_characters(value):
    """Checks if a UK establishment number only has valid characters."""
    return not value or not _INVALID_COMPANY_NUMBER_RE.search(value)
