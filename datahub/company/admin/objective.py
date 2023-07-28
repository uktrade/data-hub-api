from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.company.models import Objective
from datahub.core.admin import BaseModelAdminMixin


@admin.register(Objective)
class ObjectiveAdmin(BaseModelAdminMixin, VersionAdmin):
    """Objective admin."""

    search_fields = (
        'pk',
        'subject',
        'detail',
        'target_date',
        'has_blocker',
        'blocker_description',
        'progress',
    )
    raw_id_fields = (
        'company',
        'archived_by',
    )
    list_display = (
        'subject',
        'company',
        'target_date',
    )
    list_select_related = ('company',)
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
