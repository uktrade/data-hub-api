from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin, DisabledOnFilter
from .models import CommunicationChannel, Interaction


@admin.register(CommunicationChannel)
class MetadataAdmin(admin.ModelAdmin):
    """Communication channel admin."""

    fields = ('name', 'disabled_on', )
    list_display = ('name', 'disabled_on', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(Interaction)
class InteractionAdmin(BaseModelVersionAdmin):
    """Interaction admin."""

    search_fields = (
        'id',
        'subject',
        'company__name',
    )
    list_display = (
        '__str__',
        'date',
        'company',
        'contact',
        'investment_project',
    )
    list_filter = (
        'kind',
    )
    raw_id_fields = (
        'company',
        'event',
        'dit_adviser',
        'investment_project',
        'contact',
        'created_by',
        'modified_by',
    )
    readonly_fields = (
        'archived_documents_url_path',
    )
    list_select_related = (
        'company',
        'contact',
        'investment_project',
        'investment_project__investor_company',
    )
