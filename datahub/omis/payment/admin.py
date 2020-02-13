from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.template.defaultfilters import date as date_formatter
from django.utils.translation import gettext_lazy as _

from datahub.core.admin import BaseModelAdminMixin
from datahub.omis.order.constants import OrderStatus
from datahub.omis.payment.constants import RefundStatus
from datahub.omis.payment.models import Refund


class RefundForm(forms.ModelForm):
    """Form for adding/changing refund records via the django admin."""

    APPROVED_MANDATORY_FIELDS = [
        'level1_approved_on',
        'level1_approved_by',
        'level2_approved_on',
        'level2_approved_by',
        'method',
        'net_amount',
        'vat_amount',
    ]

    class Meta:
        model = Refund
        fields = (
            'id',
            'order',
            'reference',
            'status',
            'requested_on',
            'requested_by',
            'requested_amount',
            'refund_reason',
            'level1_approved_on',
            'level1_approved_by',
            'level1_approval_notes',
            'level2_approved_on',
            'level2_approved_by',
            'level2_approval_notes',
            'method',
            'net_amount',
            'vat_amount',
            'total_amount',
            'rejection_reason',
            'additional_reference',
        )

    def __init__(self, *args, **kwargs):
        """
        Initialise the object.

        During the creation step, the value of status can only be RefundStatus.APPROVED.
        During the editing step, the value of status cannot be changed any longer.
        """
        super().__init__(*args, **kwargs)

        # set up the status field
        refund_status = self.instance.status or RefundStatus.APPROVED

        self.fields['status'].choices = (
            (refund_status, RefundStatus(refund_status).label),
        )

        # set up mandatory fields when status == approved
        if refund_status == RefundStatus.APPROVED:
            for field_name in self.APPROVED_MANDATORY_FIELDS:
                self.fields[field_name].required = True

    def _clean_order_status(self):
        """Validate the order data value from the `clean` method."""
        order = self.cleaned_data.get('order')
        if not order:
            return
        if order.status not in (OrderStatus.COMPLETE, OrderStatus.PAID, OrderStatus.CANCELLED):
            self.add_error(
                'order',
                ValidationError(_('This order has not been paid for.'), code='not_paid'),
            )

    def _clean_datetime_field_gte_value(self, field, compared_value):
        """Validate a datetime data value from the `clean` method."""
        field_value = self.cleaned_data.get(field)
        if not field_value or not compared_value:
            return

        if field_value < compared_value:
            self.add_error(
                field,
                ValidationError(
                    _('Please specify a value greater than or equal to %(compared_value)s.'),
                    params={
                        'compared_value': date_formatter(
                            compared_value, settings.DATETIME_FORMAT,
                        ),
                    },
                    code='invalid_date',
                ),
            )

    def _clean_amounts(self):
        """Validate the amount values from the `clean` method."""
        order = self.cleaned_data['order']
        net_amount = self.cleaned_data.get('net_amount')
        vat_amount = self.cleaned_data.get('vat_amount')
        if net_amount is None or vat_amount is None:
            return

        total_amount = net_amount + vat_amount

        qs = order.refunds
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        currently_refunded = sum(
            amount for amount in qs.values_list('total_amount', flat=True) if amount
        )

        refund_remaining = order.total_cost - currently_refunded
        if total_amount > refund_remaining:
            self.add_error(
                'net_amount',
                ValidationError(
                    _('Remaining amount that can be refunded: %(refund_remaining)s.'),
                    params={
                        'refund_remaining': refund_remaining,
                    },
                    code='refund_limit_exceeded',
                ),
            )
        else:
            self.cleaned_data['total_amount'] = total_amount

    def _clean_approvals(self):
        """Validate the approval data values from the `clean` method."""
        level1_approved_by = self.cleaned_data.get('level1_approved_by')
        level2_approved_by = self.cleaned_data.get('level2_approved_by')

        if level1_approved_by and level1_approved_by == level2_approved_by:
            self.add_error(
                'level1_approved_by',
                ValidationError(
                    _('Approvers level1 and level2 have to be different.'),
                    code='invalid_approvers',
                ),
            )

    def clean(self):
        """Add some extra validation on the top of the existing one."""
        super().clean()

        self._clean_order_status()
        order = self.cleaned_data.get('order')
        if not order:
            return

        self._clean_datetime_field_gte_value('requested_on', order.paid_on)
        requested_on = self.cleaned_data.get('requested_on')

        self._clean_datetime_field_gte_value('level1_approved_on', order.paid_on)
        self._clean_datetime_field_gte_value('level1_approved_on', requested_on)
        self._clean_datetime_field_gte_value('level2_approved_on', order.paid_on)
        self._clean_datetime_field_gte_value('level2_approved_on', requested_on)

        self._clean_approvals()

        self._clean_amounts()

        return self.cleaned_data


@admin.register(Refund)
class RefundAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Refund admin."""

    form = RefundForm

    search_fields = (
        'pk',
        'order__reference',
        'reference',
    )
    list_display = (
        'reference',
        'order',
        'status',
        'requested_on',
    )
    list_filter = (
        'status',
    )
    raw_id_fields = (
        'order',
        'requested_by',
        'level1_approved_by',
        'level2_approved_by',
    )
    readonly_fields = (
        'id',
        'reference',
        'created',
        'modified',
        'total_amount',
    )
    list_select_related = (
        'order',
    )

    def save_model(self, request, obj, form, change):
        """Populate total_amount from other fields."""
        if 'total_amount' in form.cleaned_data:
            obj.total_amount = form.cleaned_data['total_amount']

        super().save_model(request, obj, form, change)
