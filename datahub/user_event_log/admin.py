import json

from django.contrib import admin
from django.utils.html import format_html

from datahub.core.admin import get_change_link, ViewOnlyAdmin
from datahub.user_event_log.models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(ViewOnlyAdmin):
    """Admin configuration for UserEvent."""

    list_display = ('timestamp', 'adviser', 'type', 'api_url_path')
    list_filter = ('type', 'api_url_path')
    list_select_related = ('adviser',)
    fields = (
        'id',
        'timestamp',
        'adviser_link',
        'type',
        'api_url_path',
        'pretty_data',
    )
    readonly_fields = fields

    def adviser_link(self, obj):
        """Returns a link to the adviser."""
        return get_change_link(obj.adviser)

    adviser_link.short_description = 'adviser'

    def pretty_data(self, obj):
        """Returns the data field formatted with indentation."""
        return format_html('<pre>{0}</pre>', json.dumps(obj.data, indent=2))

    pretty_data.short_description = 'data'
