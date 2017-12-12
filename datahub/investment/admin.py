"""Admin registration for investment models."""

from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin, custom_change_permission, DisabledOnFilter
from datahub.investment.models import (
    InvestmentProject,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    IProjectDocument,
    SpecificProgramme,
)
from datahub.investment.permissions import Permissions


@admin.register(InvestmentProject)
@custom_change_permission(Permissions.change_all)
class InvestmentProjectAdmin(BaseModelVersionAdmin):
    """Investment project admin."""

    search_fields = ['name']
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
        'archived_documents_url_path',
    )


@admin.register(InvestmentProjectTeamMember)
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
