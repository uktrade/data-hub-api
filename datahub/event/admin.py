import functools

from django.contrib import admin
from django.contrib.admin import DateFieldListFilter, helpers
from django.template.response import TemplateResponse
from django.utils.timezone import now
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, DisabledOnFilter
from datahub.event.models import Event, EventType, LocationType, Programme
from datahub.metadata.admin import DisableableMetadataAdmin
from datahub.metadata.models import TradeAgreement


def confirm_action(title, action_message):
    """Decorator that adds confirmation step before modifying selected objects."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, queryset):
            if request.POST.get('confirm') == 'yes':
                updated = func(self, request, queryset)
                message = f'{updated} {self.model._meta.verbose_name_plural} updated.'
                self.message_user(request, message)
                return None

            context = dict(
                self.admin_site.each_context(request),
                title=title,
                action=func.__name__,
                action_message=action_message,
                action_checkbox_name=helpers.ACTION_CHECKBOX_NAME,
                opts=self.model._meta,
                queryset=queryset,
                media=self.media,
            )
            return TemplateResponse(request, 'admin/action_confirmation.html', context)

        return wrapper

    return decorator


@admin.register(Event)
class EventAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin for Events."""

    fields = (
        'name',
        'created',
        'modified',
        'event_type',
        'start_date',
        'end_date',
        'location_type',
        'address_1',
        'address_2',
        'address_town',
        'address_county',
        'address_postcode',
        'address_country',
        'uk_region',
        'notes',
        'organiser',
        'lead_team',
        'teams',
        'related_trade_agreements',
        'related_programmes',
        'service',
        'disabled_on',
    )
    list_display = (
        'name',
        'start_date',
        'end_date',
        'lead_team',
        'service',
        'disabled_on',
    )
    list_filter = (
        DisabledOnFilter,
        ('start_date', DateFieldListFilter),
    )
    readonly_fields = (
        'id',
        'created',
        'modified',
        'archived_documents_url_path',
    )
    search_fields = ('name', 'pk')

    raw_id_fields = (
        'lead_team',
        'teams',
        'organiser',
    )

    actions = ('disable_selected', 'enable_selected')

    @confirm_action(
        title='Disable selected events',
        action_message='disable the selected events',
    )
    def disable_selected(self, request, queryset):
        """Disables selected objects."""
        current_date = now()
        # we process records individually, so that the post_save signal
        # is being triggered
        for row in queryset:
            row.disabled_on = current_date
            row.save()

    disable_selected.short_description = 'Disable selected events'

    @confirm_action(
        title='Enable selected events',
        action_message='enable the selected events',
    )
    def enable_selected(self, request, queryset):
        """Enables selected objects."""
        # we process records individually, so that the post_save signal
        # is being triggered
        for row in queryset:
            row.disabled_on = None
            row.save()

    enable_selected.short_description = 'Enable selected events'


admin.site.register((EventType, LocationType, Programme, TradeAgreement), DisableableMetadataAdmin)
