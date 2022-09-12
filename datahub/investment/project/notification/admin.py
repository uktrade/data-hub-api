from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.investment.project.notification.models import NotificationInnerTemplate


@admin.register(NotificationInnerTemplate)
class NotificationInnerTemplateAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Notification inner template Admin."""

    list_display = ('notification_type', )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Ensure the content field retains newlines."""
        if db_field.name == 'content':
            kwargs['strip'] = False
        return super().formfield_for_dbfield(db_field, request, **kwargs)
