from django.contrib import admin

from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin
from datahub.task.models import Task


@admin.register(Task)
class TaskAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin form for tasks"""

    search_fields = (
        'pk',
        'title',
    )
    readonly_fields = (
        'id',
        'created',
    )
