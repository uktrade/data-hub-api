from django.contrib import admin
from reversion.admin import VersionAdmin

from datahub.core.admin import (
    BaseModelAdminMixin,
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
    custom_view_permission,
    format_json_as_html,
)
from datahub.core.utils import join_truthy_strings
from datahub.interaction.admin_csv_import.views import InteractionCSVImportAdmin
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionDITParticipant,
    InteractionPermission,
    PolicyArea,
    PolicyIssueType,
)
from datahub.metadata.admin import DisableableMetadataAdmin, OrderedMetadataAdmin

admin.site.register(CommunicationChannel, DisableableMetadataAdmin)
admin.site.register((PolicyArea, PolicyIssueType), OrderedMetadataAdmin)


@custom_view_permission(InteractionPermission.view_all)
@custom_add_permission(InteractionPermission.change_all)
@custom_change_permission(InteractionPermission.change_all)
@custom_delete_permission(InteractionPermission.change_all)
class InteractionDITParticipantInline(admin.TabularInline):
    """Inline admin for InteractionDITParticipant."""

    model = InteractionDITParticipant
    min_num = 1
    extra = 0

    fields = ('adviser', 'team')
    autocomplete_fields = ('adviser', 'team')

    verbose_name = 'DIT participant'
    # Note: verbose_name_plural does not get automatically updated here if verbose_name is set,
    # so we have to set it manually
    verbose_name_plural = 'DIT participants'


@admin.register(Interaction)
@custom_add_permission(InteractionPermission.add_all)
@custom_change_permission(InteractionPermission.change_all)
@custom_view_permission(InteractionPermission.view_all)
class InteractionAdmin(BaseModelAdminMixin, VersionAdmin):
    """Interaction admin."""

    autocomplete_fields = ('contacts', 'companies')
    inlines = (
        InteractionDITParticipantInline,
    )
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
        'investment_project',
    )
    readonly_fields = (
        'archived_documents_url_path',
        'created',
        'modified',
        'pretty_service_answers',
        'pretty_source',
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
        'service_answers',
        'source',
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

    def pretty_source(self, obj):
        """
        Return the source field formatted with indentation.
        """
        return format_json_as_html(obj.source)

    pretty_source.short_description = 'source'

    def pretty_service_answers(self, obj):
        """Return the service_answers field formatted with indentation."""
        return format_json_as_html(obj.service_answers)

    pretty_service_answers.short_description = 'service answers'

    def get_urls(self):
        """Gets the URLs for this model's admin views."""
        csv_importer = InteractionCSVImportAdmin(self)

        return [
            *super().get_urls(),
            *csv_importer.get_urls(),
        ]
