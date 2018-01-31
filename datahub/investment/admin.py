"""Admin registration for investment models."""

from django.contrib import admin

from datahub.core.admin import (
    BaseModelVersionAdmin, custom_add_permission, custom_change_permission,
    custom_delete_permission, DisabledOnFilter,
)
from datahub.investment.models import (
    InvestmentDeliveryPartner,
    InvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    IProjectDocument,
    SpecificProgramme,
)


@admin.register(InvestmentProject)
@custom_change_permission(InvestmentProjectPermission.change_all)
class InvestmentProjectAdmin(BaseModelVersionAdmin):
    """Investment project admin."""

    search_fields = (
        '=pk',
        'name',
    )
    raw_id_fields = (
        'archived_by',
        'associated_non_fdi_r_and_d_project',
        'investor_company',
        'intermediate_company',
        'client_contacts',
        'client_relationship_manager',
        'referral_source_adviser',
        'project_manager',
        'project_assurance_adviser',
        'uk_company',
        'created_by',
        'modified_by',
    )
    readonly_fields = (
        'allow_blank_estimated_land_date',
        'allow_blank_possible_uk_regions',
        'archived_documents_url_path',
        'comments',
    )


@admin.register(InvestmentProjectTeamMember)
@custom_add_permission(InvestmentProjectPermission.change_all)
@custom_change_permission(InvestmentProjectPermission.change_all)
@custom_delete_permission(InvestmentProjectPermission.change_all)
class InvestmentProjectTeamMemberAdmin(BaseModelVersionAdmin):
    """Investment project team member admin."""

    raw_id_fields = (
        'investment_project',
        'adviser',
    )


@admin.register(IProjectDocument)
class IProjectDocumentAdmin(admin.ModelAdmin):
    """Investment project document admin."""

    list_display = (
        'id', 'doc_type', 'filename'
    )
    list_filter = (
        'doc_type',
    )
    raw_id_fields = (
        'archived_by',
        'project',
        'document',
        'created_by',
        'modified_by',
    )
    date_hierarchy = 'created_on'


@admin.register(
    InvestmentDeliveryPartner,
    InvestorType,
    Involvement,
    SpecificProgramme,
)
class DisableableMetadataAdmin(admin.ModelAdmin):
    """Custom Disableable Metadata Admin."""

    fields = ('id', 'name', 'disabled_on',)
    list_display = ('name', 'disabled_on',)
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')
    list_filter = (DisabledOnFilter,)
