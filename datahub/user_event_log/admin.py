from django.contrib import admin

from datahub.core.admin import ViewOnlyAdmin, format_json_as_html, get_change_link
from datahub.user_event_log.models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(ViewOnlyAdmin):
    """Admin configuration for UserEvent."""

    list_display = ('timestamp', 'adviser', 'type', 'api_url_path')
    list_filter = ('type',)
    list_select_related = ('adviser',)
    fields = (
        'id',
        'timestamp',
        'adviser_link',
        'type',
        'api_url_path',
        'pretty_data',
    )
    search_fields = ('^api_url_path', '=adviser__id')
    readonly_fields = fields

    @admin.display(
        description='adviser',
    )
    def adviser_link(self, obj):
        """Returns a link to the adviser."""
        return get_change_link(obj.adviser)

    @admin.display(
        description='data',
    )
    def pretty_data(self, obj):
        """Returns the data field formatted with indentation."""
        return format_json_as_html(obj.data)
