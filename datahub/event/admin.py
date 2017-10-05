import functools
from datetime import datetime

from django.contrib import admin
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

from datahub.core.admin import BaseModelVersionAdmin
from datahub.event.models import Event, EventType, LocationType, Programme


class DisabledOnFilter(admin.SimpleListFilter):
    """This filter allows us to filter values that have disabled_on value."""

    title = 'Is disabled'
    parameter_name = 'disabled_on'

    def lookups(self, request, model_admin):
        """Returns parameters."""
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        """Modify query according to filter parameter."""
        value = self.value()
        if value is not None:
            is_disabled = True if value == 'yes' else False
            return queryset.filter(disabled_on__isnull=is_disabled)
        return queryset


def confirm_action(title, action_message):
    """Decorator that adds confirmation step before modifying selected objects."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, queryset):
            if request.POST.get('confirm') == 'yes':
                updated = func(self, request, queryset)
                self.message_user(request, f'{updated} objects updated.')
                return None

            context = dict(
                self.admin_site.each_context(request),
                title=title,
                action=func.__name__,
                action_message=action_message,
                action_checkbox_name=helpers.ACTION_CHECKBOX_NAME,
                opts=self.model._meta,
                queryset=queryset,
            )
            return TemplateResponse(request, 'admin/action_confirmation.html', context)

        return wrapper

    return decorator


@admin.register(Event)
class EventAdmin(BaseModelVersionAdmin):
    """Admin for Events."""

    fields = (
        'name',
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
        'related_programmes',
        'service',
        'disabled_on',
    )
    list_display = ('name', 'disabled_on',)
    list_editable = ('disabled_on',)
    list_filter = (DisabledOnFilter,)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')

    raw_id_fields = (
        'lead_team',
        'teams',
        'organiser',
        'modified_by',
        'created_by',
    )

    actions = ('disable_selected', 'enable_selected',)

    @confirm_action(
        title='Disable selected',
        action_message='disable selected'
    )
    def disable_selected(self, request, queryset):
        """Disables selected objects."""
        return queryset.update(disabled_on=datetime.utcnow())

    disable_selected.short_description = 'Disable selected'

    @confirm_action(
        title='Enable selected',
        action_message='enable selected'
    )
    def enable_selected(self, request, queryset):
        """Enables selected objects."""
        return queryset.update(disabled_on=None)

    enable_selected.short_description = 'Enable selected'


@admin.register(EventType, LocationType, Programme)
class MetadataAdmin(admin.ModelAdmin):
    """Admin for metadata models."""

    fields = ('name',)
    list_display = ('name',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
