from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, custom_add_permission, custom_change_permission
from datahub.core.query_utils import get_full_name_expression, get_string_agg_subquery
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
        'contacts',
    )
    readonly_fields = (
        'archived_documents_url_path',
        'created',
        'modified',
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

    def get_queryset(self, request):
        """Annotates the query set with contact names as a comma-separated string."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            contact_names=get_string_agg_subquery(
                Interaction,
                get_full_name_expression('contacts'),
            ),
        )

    def get_contact_names(self, obj):
        """Returns contact names for the interaction as a comma-separated string."""
        return obj.contact_names

    get_contact_names.short_description = 'contacts'
    get_contact_names.admin_order_field = 'contact_names'

    def save_model(self, request, obj, form, change):
        """
        Saves the object, populating contacts from contact.

        TODO: Remove once the migration from contact to contacts is complete.
        """
        if 'contacts' in form.cleaned_data:
            contacts = form.cleaned_data['contacts']
            obj.contact = contacts[0] if contacts else None

        super().save_model(request, obj, form, change)
