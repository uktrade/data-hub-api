from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.core.admin import custom_add_permission, custom_change_permission, DisabledOnFilter
from datahub.interaction.models import InteractionPermission
from .models import CommunicationChannel, Interaction


@admin.register(CommunicationChannel)
class MetadataAdmin(admin.ModelAdmin):
    """Communication channel admin."""

    fields = ('id', 'name', 'disabled_on', )
    list_display = ('name', 'disabled_on', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)


@admin.register(Interaction)
@custom_add_permission(InteractionPermission.add_all)
@custom_change_permission(InteractionPermission.change_all)
class InteractionAdmin(VersionAdmin):
    """Interaction admin."""

    search_fields = (
        '=pk',
        'subject',
        'company__name',
    )
    list_display = (
        'subject',
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
