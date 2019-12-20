from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner


class AddressValidator:
    """Validator for addresses."""

    requires_context = True
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

    def __call__(self, data, serializer):
        """Validate the address fields."""
        instance = getattr(serializer, 'instance', None)
        data_combiner = DataCombiner(instance, data)

        data_combined = {
            field_name: data_combiner.get_value(field_name)
            for field_name in self.fields_mapping.keys()
        }

        if not self._should_validate(data_combined):
            return

        errors = self._validate_fields(data_combined)
        if errors:
            raise ValidationError(errors)
