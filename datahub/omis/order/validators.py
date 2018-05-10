from collections import defaultdict

from django.db import models
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from datahub.core.exceptions import APIConflictException
from datahub.core.validate_utils import DataCombiner
from datahub.core.validators import AbstractRule, BaseRule
from .constants import OrderStatus, VATStatus


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


class OrderEditableFieldsValidator:
    """
    Validator that makes sure that only certain fields have been modified
    depending on the order status.
    """

    message = 'This field cannot be changed at this stage.'

    def __init__(self, mapping=None):
        """
        Set the mapping.

        :param mapping: dict of <order status, editable fields>
        """
        self.mapping = mapping or {}
        self.instance = None

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer, 'instance', None)

    def _has_changed(self, field, combiner):
        """
        :returns: True if the data value for `field` has changed compared to
            its instance value.
        """
        field_value = combiner.get_value_auto(field)
        instance_value = DataCombiner(
            self.instance, {},
            model=self.instance.__class__
        ).get_value_auto(field)

        # if it's a queryset, evaluate it
        if hasattr(instance_value, 'all'):
            instance_value = list(instance_value)

        return field_value != instance_value

    def __call__(self, data):
        """Validate editable fields depending on the order status."""
        if not self.instance or self.instance.status not in self.mapping:
            return

        combiner = DataCombiner(self.instance, data, model=self.instance.__class__)

        editable_fields = self.mapping[self.instance.status]
        for field in combiner.data:
            if field not in editable_fields and self._has_changed(field, combiner):
                raise ValidationError({field: self.message})


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
    no_lead_assignee_message = 'You need to set a lead assignee.'
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

        if not self.instance.assignees.filter(is_lead=True).count():
            raise ValidationError({
                'assignee_lead': [self.no_lead_assignee_message]
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
            raise APIConflictException(self.message)


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

        if self.instance.status not in self.allowed_statuses:
            raise APIConflictException(
                self.message.format(self.instance.get_status_display())
            )


class CompletableOrderValidator:
    """
    Validator which checks that the order can be completed, that is,
    all the assignees have their actual_time field set.
    """

    message = 'You must set the actual time for all assignees to complete this order.'

    def __init__(self):
        """Initialise the object."""
        self.order = None

    def set_order(self, order):
        """Set the order attr to the selected one."""
        self.order = order

    def __call__(self):
        """Validate that the actual_time field for all the assignees is set."""
        if any(assignee.actual_time is None for assignee in self.order.assignees.all()):
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: self.message
            })


class CancellableOrderValidator(OrderInStatusValidator):
    """Validator which checks that the order can be cancelled."""

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
