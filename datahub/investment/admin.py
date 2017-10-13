"""Admin registration for investment models."""

from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin
from datahub.investment.models import (InvestmentProject, InvestmentProjectTeamMember,
                                       IProjectDocument)


@admin.register(InvestmentProject)
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
