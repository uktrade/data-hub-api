from collections import defaultdict

from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from datahub.core.exceptions import APIConflictException
from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import AbstractRule, BaseRule
from datahub.omis.order.constants import OrderStatus, VATStatus


class ContactWorksAtCompanyValidator:
    """Validator which checks if contact works at the specified company."""

    requires_context = True
    message = 'The contact does not work at the given company.'

    def __init__(self, contact_field='contact', company_field='company'):
        """Set the fields."""
        self.contact_field = contact_field
        self.company_field = company_field

    def __call__(self, data, serializer):
        """Validate that contact works at company."""
        instance = getattr(serializer, 'instance', None)
        data_combiner = DataCombiner(instance, data)
        company = data_combiner.get_value(self.company_field)
        contact = data_combiner.get_value(self.contact_field)

        if contact.company != company:
            raise ValidationError({
                self.contact_field: self.message,
            })


class OrderEditableFieldsValidator:
    """
    Validator that makes sure that only certain fields have been modified
    depending on the order status.
    """

    requires_context = True
    message = 'This field cannot be changed at this stage.'

    def __init__(self, mapping=None):
        """
        Set the mapping.

        :param mapping: dict of <order status, editable fields>
        """
        self.mapping = mapping or {}

    @staticmethod
    def _has_changed(field, combiner):
        """
        :returns: True if the data value for `field` has changed compared to
            its instance value.
        """
        field_value = combiner.get_value_auto(field)
        instance_value = DataCombiner(
            combiner.instance, {},
            model=combiner.instance.__class__,
        ).get_value_auto(field)

        # if it's a queryset, evaluate it
        if hasattr(instance_value, 'all'):
            instance_value = list(instance_value)

        return field_value != instance_value

    def __call__(self, data, serializer):
        """Validate editable fields depending on the order status."""
        instance = getattr(serializer, 'instance', None)

        if not instance or instance.status not in self.mapping:
            return

        combiner = DataCombiner(instance, data, model=instance.__class__)

        editable_fields = self.mapping[instance.status]
        for field in combiner.data:
            if field not in editable_fields and self._has_changed(field, combiner):
                raise ValidationError({field: self.message})


class VATSubValidator:
    """
    Validator for checking VAT fields on the order.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    message = 'This field is required.'

    def __call__(self, data=None, order=None):
        """
        Check that:
        - vat_status is specified
        - if vat_status == eu:
            - vat_verified is specified
            - if vat_verified == True:
                - vat_number is specified
        """
        data_combiner = DataCombiner(order, data)

        vat_status = data_combiner.get_value('vat_status')
        if not vat_status:
            raise ValidationError({
                'vat_status': [self.message],
            })

        if vat_status == VATStatus.eu:
            vat_verified = data_combiner.get_value('vat_verified')
            if vat_verified is None:
                raise ValidationError({
                    'vat_verified': [self.message],
                })

            vat_number = data_combiner.get_value('vat_number')
            if vat_verified and not vat_number:
                raise ValidationError({
                    'vat_number': [self.message],
                })


class AssigneesFilledInSubValidator:
    """
    Validator which checks that the order has enough information about assignees.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    no_assignees_message = 'You need to add at least one assignee.'
    no_lead_assignee_message = 'You need to set a lead assignee.'
    no_estimated_time_message = 'The total estimated time cannot be zero.'

    def __call__(self, data=None, order=None):
        """Validate that the information about the assignees is set."""
        if not order.assignees.count():
            raise ValidationError({
                'assignees': [self.no_assignees_message],
            })

        if not order.assignees.filter(is_lead=True).count():
            raise ValidationError({
                'assignee_lead': [self.no_lead_assignee_message],
            })

        if not order.assignees.aggregate(sum=models.Sum('estimated_time'))['sum']:
            raise ValidationError({
                'assignee_time': [self.no_estimated_time_message],
            })


class OrderDetailsFilledInSubValidator:
    """
    Validator which checks that the order has all detail fields filled in.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    REQUIRED_FIELDS = (
        'primary_market',
        'service_types',
        'description',
        'delivery_date',
    )

    extra_validators = (
        VATSubValidator(),
        AssigneesFilledInSubValidator(),
    )

    message = 'This field is required.'

    def get_extra_validators(self):
        """
        Useful for subclassing or testing.

        :returns: the extra_validators.
        """
        return self.extra_validators

    def _run_extra_validators(self, data, order):
        """
        Run the extra validators against the instance/data.

        :returns: errors dict, either filled in or empty
        """
        errors = defaultdict(list)
        for validator in self.get_extra_validators():
            try:
                validator(data=data, order=order)
            except ValidationError as exc:
                for field, field_errors in exc.detail.items():
                    errors[field] += field_errors
        return errors

    def __call__(self, data=None, order=None):
        """Validate that all the fields required are set."""
        data_combiner = DataCombiner(order, data)

        meta = order._meta
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
        extra_errors = self._run_extra_validators(data, order)
        for field, field_errors in extra_errors.items():
            errors[field] += field_errors

        if errors:
            raise ValidationError(errors)


class NoOtherActiveQuoteExistsSubValidator:
    """
    Validator which checks that there's no other active quote.
    Used to check whether a new quote for the specified order can be
    generated.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    message = "There's already an active quote."

    def __call__(self, data=None, order=None):
        """Validate that no other active quote exists."""
        if order.quote and not order.quote.is_cancelled():
            raise APIConflictException(self.message)


class OrderInStatusSubValidator:
    """
    Validator which checks that the order is in one of the given statuses.

    This validator is designed for direct use rather than with a DRF serializer.
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

    def __call__(self, data=None, order=None):
        """Validate that the order is in one of the statuses."""
        if not order and not self.order_required:
            return  # all fine

        if order.status not in self.allowed_statuses:
            raise APIConflictException(
                self.message.format(order.get_status_display()),
            )


class OrderInStatusValidator:
    """
    Validator which checks that the order is in one of the given statuses.
    """

    requires_context = True

    def __init__(self, allowed_statuses, order_required=True):
        """
        :param allowed_statuses: list of OrderStatus values allowed
        :param order_required: if False and the order is None, the validation passes,
            useful when creating orders
        """
        self.sub_validator = OrderInStatusSubValidator(
            allowed_statuses,
            order_required=order_required,
        )

    def __call__(self, data, serializer):
        """
        Validate that the order is in one of the statuses.

        An order instance is searched for in the following locations (using the first one found):
        - serializer.context['order]
        - serializer.instance
        """
        instance = serializer.context.get('order', serializer.instance)
        self.sub_validator(data=data, order=instance)


class CompletableOrderSubValidator:
    """
    Validator which checks that the order can be completed, that is,
    all the assignees have their actual_time field set.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    message = 'You must set the actual time for all assignees to complete this order.'

    def __call__(self, data=None, order=None):
        """Validate that the actual_time field for all the assignees is set."""
        if any(assignee.actual_time is None for assignee in order.assignees.all()):
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: self.message,
            })


class CancellableOrderSubValidator(OrderInStatusSubValidator):
    """
    Validator which checks that the order can be cancelled.

    This validator is designed for direct use rather than with a DRF serializer.
    """

    def __init__(self, force=False):
        """
        :param force: if True, cancelling an order in quote accepted or paid
            is allowed.
        """
        allowed_statuses = [
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
        ]
        if force:
            allowed_statuses += [
                OrderStatus.quote_accepted,
                OrderStatus.paid,
            ]
        super().__init__(allowed_statuses, order_required=True)


class OrderInStatusRule(AbstractRule):
    """Rule for checking that an order is in the expected state."""

    def __init__(self, order_statuses):
        """Initialise the rule."""
        self.order_statuses = order_statuses

    @property
    def field(self):
        """Field property not needed."""
        return None

    def __call__(self, combiner):
        """Check that order is in the expected state."""
        if 'order' in combiner.serializer.context:
            order = combiner.serializer.context['order']
        else:
            order = combiner.serializer.instance

        if not order:
            return False
        return order.status in self.order_statuses


class ForceDeleteRule(BaseRule):
    """Rule for checking that the force_delete flag has the expected value."""

    def __init__(self, field, value):
        """Initialise the rule."""
        super().__init__(field)
        self.value = value

    def __call__(self, combiner):
        """Check that the force_delete flag has the expected value."""
        return combiner.serializer.context.get('force_delete', False) == self.value
