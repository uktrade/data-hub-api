from django.contrib import admin
from django.db.transaction import atomic
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, custom_add_permission, custom_change_permission
from datahub.core.utils import join_truthy_strings
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

    autocomplete_fields = ('contacts',)
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
        'get_contact_names',
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
    )
    readonly_fields = (
        'archived_documents_url_path',
        'created',
        'modified',
        'dit_adviser',
        'dit_team',
    )
    list_select_related = (
        'company',
        'investment_project',
        'investment_project__investor_company',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
        'contact',
    )

    def get_contact_names(self, obj):
        """Returns contact names for the interaction as a formatted string."""
        contact_queryset = obj.contacts.order_by('pk')

        # Deliberate use of len() to force the query set to be evaluated (so that contact_count
        # and first_contact are consistent)
        contact_count = len(contact_queryset)
        first_contact = contact_queryset[0] if contact_count else None

        return join_truthy_strings(
            first_contact.name if first_contact else '',
            f'and {contact_count - 1} more' if contact_count > 1 else '',
        )

    get_contact_names.short_description = 'contacts'

    @atomic
    def save_model(self, request, obj, form, change):
        """
        Saves the object, while also:
            - copying contacts to contact
            - copying dit_adviser and dit_team to dit_participants
        """
        # TODO: Remove once the migration from contact to contacts is complete.
        if 'contacts' in form.cleaned_data:
            contacts = form.cleaned_data['contacts']
            obj.contact = contacts[0] if contacts else None

        super().save_model(request, obj, form, change)
