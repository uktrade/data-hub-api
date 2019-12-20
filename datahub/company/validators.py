import re

from rest_framework.exceptions import ValidationError

_INVALID_COMPANY_NUMBER_RE = re.compile(r'[^A-Z0-9]')


class NotATransferredCompanyValidator:
    """Validates that a company has not been marked as a duplicate."""

    requires_context = True

    def __call__(self, data, serializer):
        """Performs validation."""
        instance = serializer.instance

        if instance.transferred_to:
            transfer_reason = instance.get_transfer_reason_display()
            raise ValidationError(
                f'This record is no longer in use and its data has been transferred to another '
                f'record for the following reason: {transfer_reason}.',
                'transferred_company',
            )


def has_uk_establishment_number_prefix(value):
    """Checks if a UK establishment number has the correct (BR) prefix."""
    return not value or value.startswith('BR')


def has_no_invalid_company_number_characters(value):
    """Checks if a UK establishment number only has valid characters."""
    return not value or not _INVALID_COMPANY_NUMBER_RE.search(value)
