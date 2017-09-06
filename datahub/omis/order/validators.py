from django.db import models

from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.omis.core.exceptions import Conflict


class ContactWorksAtCompanyValidator:
    """Validator which checks if contact works at the specified company."""

    message = 'The contact does not work at the given company.'

    def __init__(self, contact_field='contact', company_field='company'):
        """Set the fields."""
        self.contact_field = contact_field
        self.company_field = company_field

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer, 'instance', None)

    def __call__(self, data):
        """Validate that contact works at company."""
        data_combiner = DataCombiner(self.instance, data)
        company = data_combiner.get_value(self.company_field)
        contact = data_combiner.get_value(self.contact_field)

        if contact.company != company:
            raise ValidationError({
                self.contact_field: self.message
            })


class ReadonlyAfterCreationValidator:
    """
    Validator which checks that the specified fields become readonly
    after creation.
    """

    message = 'The {0} cannot be changed after creation.'

    def __init__(self, fields):
        """Set the fields."""
        self.fields = fields

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer, 'instance', None)

    def __call__(self, data):
        """Validate readonly fields after creation."""
        data_combiner = DataCombiner(self.instance, data)

        if self.instance:
            for field in self.fields:
                value = data_combiner.get_value(field)

                if value != getattr(self.instance, field):
                    field_name = self.instance._meta.get_field(field).verbose_name
                    raise ValidationError({
                        field: self.message.format(field_name)
                    })


class OrderDetailsFilledInValidator:
    """Validator which checks that the order has all detail fields filled in."""

    REQUIRED_FIELDS = (
        'primary_market',
        'service_types',
        'description',
        'delivery_date',
    )

    message = 'This field is required.'

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):
        """Validate that all the fields required are set."""
        data_combiner = DataCombiner(self.instance, data)

        meta = self.instance._meta
        errors = {}
        for field_name in self.REQUIRED_FIELDS:
            field = meta.get_field(field_name)

            if isinstance(field, models.ManyToManyField):
                value = data_combiner.get_value_to_many(field_name)
            else:
                value = data_combiner.get_value(field_name)

            if not value:
                errors[field_name] = [
                    self.message
                ]

        if errors:
            raise ValidationError(errors)


class NoOtherActiveQuoteExistsValidator:
    """
    Validator which checks that there's no other active quote.
    Used to check whether a new quote for the specified order can be
    generated.
    """

    message = "There's already an active quote."

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):
        """Validate that no other active quote exists."""
        if self.instance.quote and not self.instance.quote.is_cancelled():
            raise Conflict(self.message)
