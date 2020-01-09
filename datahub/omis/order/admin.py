from functools import update_wrapper

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.exceptions import SuspiciousOperation
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.html import format_html, format_html_join
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect

from datahub.core.admin import (
    BaseModelAdminMixin,
    get_change_link,
    get_change_url,
    ViewAndChangeOnlyAdmin,
)
from datahub.core.exceptions import APIConflictException
from datahub.omis.order import validators
from datahub.omis.order.models import CancellationReason, Order

csrf_protect_m = method_decorator(csrf_protect)


class CancelOrderForm(forms.Form):
    """Admin form to cancel an order."""

    reason = forms.ModelChoiceField(
        queryset=CancellationReason.objects.filter(disabled_on__isnull=True),
    )

    def __init__(self, order, *args, **kwargs):
        """Initiate the form with an instance of the order."""
        self.order = order
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validate the form."""
        cleaned_data = super().clean()

        validator = validators.CancellableOrderSubValidator(force=True)
        try:
            validator(order=self.order)
        except APIConflictException as e:
            raise forms.ValidationError(e)

        return cleaned_data

    def cancel(self, by):
        """Cancel the order after validating the data."""
        self.order.cancel(
            by=by,
            reason=self.cleaned_data['reason'],
            force=True,
        )


@admin.register(Order)
class OrderAdmin(BaseModelAdminMixin, ViewAndChangeOnlyAdmin):
    """Admin for orders."""

    list_display = ('reference', 'company', 'status', 'created_on', 'modified_on')
    search_fields = ('reference', 'invoice__invoice_number')
    list_filter = ('status',)

    readonly_fields = (
        'id',
        'reference',
        'invoice_link',
        'created',
        'modified',
        'public_token',
        'public_facing_url',
        'company',
        'contact',
        'contact_email',
        'contact_phone',
        'primary_market',
        'status',
        'paid_on',
        'completed',
        'cancelled',
        'service_types',
        'description',
        'contacts_not_to_approach',
        'further_info',
        'existing_agents',
        'product_info',
        'permission_to_approach_contacts',
        'delivery_date',
        'po_number',
        'hourly_rate',
        'discount',
        'vat_status',
        'vat_number',
        'vat_verified',
        'net_cost',
        'subtotal_cost',
        'vat_cost',
        'total_cost',
        'billing_company_name',
        'billing_contact_name',
        'billing_email',
        'billing_phone',
        'billing_address_1',
        'billing_address_2',
        'billing_address_town',
        'billing_address_county',
        'billing_address_postcode',
        'billing_address_country',
        'archived_documents_url_path',
        'uk_advisers',
        'post_advisers',
    )
    _editable_fields = ('sector', 'uk_region')
    fields = readonly_fields + _editable_fields

    def invoice_link(self, obj):
        """Returns a link to the invoice change page."""
        if obj.invoice:
            return get_change_link(obj.invoice)
        return ''

    invoice_link.short_description = 'Current invoice'

    def completed(self, order):
        """:returns: completed on/by details."""
        if not order.completed_on and not order.completed_by:
            return ''
        return self._get_description_for_timed_event(order.completed_on, order.completed_by)

    def cancelled(self, order):
        """:returns: cancelled on/by/why details."""
        if not order.cancelled_on and not order.cancelled_by and not order.cancellation_reason:
            return ''
        description = self._get_description_for_timed_event(
            order.cancelled_on, order.cancelled_by,
        )

        return f'{description} because "{order.cancellation_reason}"'

    def public_facing_url(self, order):
        """
        :returns: read-only and clickable URL to the public facing OMIS page
        """
        url = order.get_public_facing_url()
        return format_html('<a href="{href}">{text}<a>', href=url, text=url)

    def discount(self, order):
        """
        :returns: details of any discount applied
        """
        if not order.discount_value and not order.discount_label:
            return ''
        return f'{order.discount_value} pence - {order.discount_label}'

    def uk_advisers(self, order):
        """
        :returns: descriptive list of advisers subscribed to the order
        """
        return format_html_join(
            '', '<p>{0}</p>',
            ((sub.adviser.name,) for sub in order.subscribers.all()),
        )

    def post_advisers(self, order):
        """
        :returns: descriptive list of advisers assigned to the order
        """
        return format_html_join(
            '', '<p>{0} {1}- estimated time {2} mins - actual time {3} mins</p>',
            ((
                assignee.adviser.name,
                '(lead) ' if assignee.is_lead else '',
                assignee.estimated_time or mark_safe('<i>unknown</i>'),
                assignee.actual_time or mark_safe('<i>unknown</i>'),
            ) for assignee in order.assignees.all()),
        )

    def get_urls(self):
        """Extend the standard get_urls by adding extra urls."""
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                '<path:object_id>/cancel/', wrap(self.cancel_order_view),
                name='%s_%s_cancel' % info,
            ),
        ] + urls

    @csrf_protect_m
    def cancel_order_view(self, request, object_id, extra_context=None):
        """Admin view for cancelling an order."""
        if (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET):
            raise SuspiciousOperation('Action not allowed in popup')

        with transaction.atomic(using=router.db_for_write(self.model)):
            opts = self.model._meta
            obj = self.get_object(request, unquote(object_id))

            if not self.has_change_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, opts, object_id)

            if request.POST:
                form = CancelOrderForm(obj, request.POST)

                if form.is_valid():
                    self.log_change(
                        request,
                        obj,
                        f'Cancelled because {form.cleaned_data["reason"].name}.',
                    )
                    form.cancel(by=request.user)
                    return self.response_cancel(request, obj)
            else:
                form = CancelOrderForm(obj)

            context = dict(
                self.admin_site.each_context(request),
                title=_('Are you sure?'),
                object_name=force_str(opts.verbose_name),
                object=obj,
                opts=opts,
                app_label=opts.app_label,
                preserved_filters=self.get_preserved_filters(request),
                form=form,
                is_popup=False,
                is_popup_var=IS_POPUP_VAR,
                media=self.media,
            )
            context.update(extra_context or {})

            request.current_app = self.admin_site.name
            return TemplateResponse(request, 'admin/order/cancel_confirmation.html', context)

    def response_cancel(self, request, obj):
        """Determine the HttpResponse for the cancel_order_view stage."""
        opts = self.model._meta

        msg_dict = {
            'name': force_str(opts.verbose_name),
            'obj': format_html('<a href="{0}">{1}</a>', urlquote(request.path), obj),
        }
        msg = format_html(
            _('The {name} "{obj}" was cancelled successfully.'),
            **msg_dict,
        )
        self.message_user(request, msg, messages.SUCCESS)

        preserved_filters = self.get_preserved_filters(request)
        redirect_url = add_preserved_filters(
            {'preserved_filters': preserved_filters, 'opts': opts},
            get_change_url(obj),
        )
        return HttpResponseRedirect(redirect_url)
