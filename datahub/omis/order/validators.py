from collections import defaultdict
from django.db import models

from rest_framework.exceptions import ValidationError

from datahub.core.validate_utils import DataCombiner
from datahub.omis.core.exceptions import Conflict

from .constants import VATStatus


class ContactWorksAtCompanyValidator:
    """Validator which checks if contact works at the specified company."""

    message = 'The contact does not work at the given company.'

    def __init__(self, contact_field='contact', company_field='company'):
        """Set the fields."""
        self.contact_field = contact_field
        self.company_field = company_field
        self.instance = None

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
        self.instance = None

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


class VATValidator:
    """Validator for checking VAT fields on the order."""

    message = 'This field is required.'

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):
        """
        Check that:
        - vat_status is specified
        - if vat_status == eu:
            - vat_verified is specified
            - if vat_verified == True:
                - vat_number is specified
        """
        data_combiner = DataCombiner(self.instance, data)

        vat_status = data_combiner.get_value('vat_status')
        if not vat_status:
            raise ValidationError({
                'vat_status': [self.message]
            })

        if vat_status == VATStatus.eu:
            vat_verified = data_combiner.get_value('vat_verified')
            if vat_verified is None:
                raise ValidationError({
                    'vat_verified': [self.message]
                })

            vat_number = data_combiner.get_value('vat_number')
            if vat_verified and not vat_number:
                raise ValidationError({
                    'vat_number': [self.message]
                })


class AssigneesFilledInValidator:
    """Validator which checks that the order has enough information about assignees."""

    no_assignees_message = 'You need to add at least one assignee.'
    no_estimated_time_message = 'The total estimated time cannot be zero.'

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):
        """Validate that the information about the assignees is set."""
        if not self.instance.assignees.count():
            raise ValidationError({
                'assignees': [self.no_assignees_message]
            })

        if not self.instance.assignees.aggregate(sum=models.Sum('estimated_time'))['sum']:
            raise ValidationError({
                'assignee_time': [self.no_estimated_time_message]
            })


class OrderDetailsFilledInValidator:
    """Validator which checks that the order has all detail fields filled in."""

    REQUIRED_FIELDS = (
        'primary_market',
        'service_types',
        'description',
        'delivery_date',
    )

    extra_validators = (
        VATValidator(),
        AssigneesFilledInValidator(),
    )

    message = 'This field is required.'

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def get_extra_validators(self):
        """
        Useful for subclassing or testing.

        :returns: the extra_validators.
        """
        return self.extra_validators

    def _run_extra_validators(self, data):
        """
        Run the extra validators against the instance/data.

        :returns: errors dict, either filled in or empty
        """
        errors = defaultdict(list)
        for validator in self.get_extra_validators():
            validator.set_instance(self.instance)
            try:
                validator(data)
            except ValidationError as exc:
                for field, field_errors in exc.detail.items():
                    errors[field] += field_errors
        return errors

    def __call__(self, data=None):
        """Validate that all the fields required are set."""
        data_combiner = DataCombiner(self.instance, data)

        meta = self.instance._meta
        errors = defaultdict(list)

        # direct required fields
        for field_name in self.REQUIRED_FIELDS:
            field = meta.get_field(field_name)

            if isinstance(field, models.ManyToManyField):
                value = data_combiner.get_value_to_many(field_name)
            else:
                value = data_combiner.get_value(field_name)

            if not value:
                errors[field_name] = [self.message]

        # extra validators
        extra_errors = self._run_extra_validators(data)
        for field, field_errors in extra_errors.items():
            errors[field] += field_errors

        if errors:
            raise ValidationError(errors)


class NoOtherActiveQuoteExistsValidator:
    """
    Validator which checks that there's no other active quote.
    Used to check whether a new quote for the specified order can be
    generated.
    """

    message = "There's already an active quote."

    def __init__(self):
        """Constructor."""
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def __call__(self, data=None):
        """Validate that no other active quote exists."""
        if self.instance.quote and not self.instance.quote.is_cancelled():
            raise Conflict(self.message)


class OrderInStatusValidator:
    """
    Validator which checks that the order is in one of the given statuses.
    """

    message = 'The action cannot be performed in the current status {0}.'

    def __init__(self, allowed_statuses, order_required=True):
        """
        :param allowed_statuses: list of OrderStatus values allowed
        :param order_required: if False and the order is None, the validation passes,
            useful when creating orders
        """
        self.allowed_statuses = allowed_statuses
        self.order_required = order_required
        self.instance = None

    def set_instance(self, instance):
        """Set the current instance."""
        self.instance = instance

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance, prior to the validation call being made.

        It sets self.instance searching for an order in the following order:
            - serializer.context['order]
            - serializer.instance
        """
        if 'order' in serializer.context:
            self.set_instance(serializer.context['order'])
        else:
            self.set_instance(serializer.instance)

    def __call__(self, data=None):
        """Validate that the order is in one of the statuses."""
        if not self.instance and not self.order_required:
            return  # all fine

        allowed = any(
            self.instance.status == status
            for status in self.allowed_statuses
        )

        if not allowed:
            raise Conflict(
                self.message.format(self.instance.get_status_display())
            )
