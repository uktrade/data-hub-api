from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.core.admin import custom_add_permission, custom_change_permission
from datahub.interaction.models import InteractionPermission, PolicyArea, PolicyIssueType
from datahub.metadata.admin import DisableableMetadataAdmin, OrderedMetadataAdmin
from .models import CommunicationChannel, Interaction


admin.site.register(CommunicationChannel, DisableableMetadataAdmin)
admin.site.register((PolicyArea, PolicyIssueType), OrderedMetadataAdmin)


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
        'created_on',
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
        'created_on',
        'modified_on',
        # TODO: Remove policy_area once policy_areas has been released
        'policy_area',
    )
    list_select_related = (
        'company',
        'contact',
        'investment_project',
        'investment_project__investor_company',
    )
