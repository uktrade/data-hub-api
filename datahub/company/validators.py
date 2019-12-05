import re

from rest_framework import serializers
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


class DuplicateExportCountryValidator:
    """
    Validates that same country is not supplied more than once
    within list of export_countries.
    """

    def __init__(self):
        """Initialises the validator."""
        self.instance = None

    def set_context(self, serializer):
        """Saves a reference to the model object."""
        self.instance = serializer.instance

    def __call__(self, data):
        """Performs validation."""
        export_countries = data.get('export_countries', None)

        if not export_countries:
            return

        deduped = set()
        for item in export_countries:
            country = item['country']
            if country in deduped:
                raise serializers.ValidationError(
                    "Same country can't be added more than once to export_countries.",
                    code='duplicate_export_country',
                )
            deduped.add(country)
