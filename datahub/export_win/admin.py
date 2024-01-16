from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin
from datahub.export_win.models import Win


@admin.register(Win)
class WinAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin for Wins."""

    list_display = (
        'company',
        'created_on',
    )
    list_filter = (
        ('created_on', DateFieldListFilter),
    )
    readonly_fields = (
        'id',
        'created_on',
        'modified_on',
    )
    search_fields = (
        'adviser__name',
        'company__name',
        'pk',
    )
    list_select_related = (
        'adviser',
        'company',
    )
    raw_id_fields = (
        'adviser',
        'company',
    )
