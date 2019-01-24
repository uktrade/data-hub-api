from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, custom_add_permission, custom_change_permission
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionPermission,
    PolicyArea,
    PolicyIssueType,
)
from datahub.metadata.admin import DisableableMetadataAdmin, OrderedMetadataAdmin


admin.site.register(CommunicationChannel, DisableableMetadataAdmin)
admin.site.register((PolicyArea, PolicyIssueType), OrderedMetadataAdmin)


@admin.register(Interaction)
@custom_add_permission(InteractionPermission.add_all)
@custom_change_permission(InteractionPermission.change_all)
class InteractionAdmin(BaseModelAdminMixin, VersionAdmin):
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
    )
    readonly_fields = (
        'archived_documents_url_path',
        'created',
        'modified',
    )
    list_select_related = (
        'company',
        'contact',
        'investment_project',
        'investment_project__investor_company',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
        'contacts',
    )

    def save_model(self, request, obj, form, change):
        """
        Saves the object, populating contacts from contact.

        TODO: Remove once the migration from contact to contacts is complete.
        """
        if 'contact' in form.cleaned_data:
            contact = form.cleaned_data['contact']
            contacts = [contact] if contact else []
            obj.contacts.set(contacts)

        super().save_model(request, obj, form, change)
