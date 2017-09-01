from django.contrib import admin

from datahub.event.models import Programme


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    """Admin for programmes."""

    fields = ('name', )
    list_display = ('name', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
