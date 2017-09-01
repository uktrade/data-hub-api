from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin
from datahub.event.models import Event, Programme


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    """Admin for programmes."""

    fields = ('name', )
    list_display = ('name', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(Event)
class InvestmentProjectAdmin(BaseModelVersionAdmin):
    """Admin for events."""

    search_fields = ['name']
    readonly_fields = (
        'id',
        'created_by',
        'modified_by',
    )
    raw_id_fields = (
        'lead_team',
        'additional_teams',
    )
