from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.investment.project.notification.models import NotificationInnerTemplate


@admin.register(NotificationInnerTemplate)
class NotificationInnerTemplateAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Notification inner template Admin."""

    list_display = ('notification_type', )
