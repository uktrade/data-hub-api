"""Admin registration for investment models."""

from django.contrib import admin
from django.utils.timezone import now
from reversion.admin import VersionAdmin

from datahub.core.admin import (
    BaseModelAdminMixin,
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
)
from datahub.investment.models import (
    InvestmentDeliveryPartner,
    InvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    LikelihoodToLand,
    ProjectManagerRequestStatus,
    SpecificProgramme,
)
from datahub.metadata.admin import (
    DisableableMetadataAdmin,
    OrderedMetadataAdmin,
    ReadOnlyMetadataAdmin,
)


@admin.register(InvestmentProject)
@custom_change_permission(InvestmentProjectPermission.change_all)
class InvestmentProjectAdmin(BaseModelAdminMixin, VersionAdmin):
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
    )
    readonly_fields = (
        'allow_blank_estimated_land_date',
        'allow_blank_possible_uk_regions',
        'archived_documents_url_path',
        'comments',
        'created',
        'modified',
    )
    list_display = (
        'name',
        'investor_company',
        'stage',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )

    def save_model(self, request, obj, form, change):
        """
        Populate who and when assigned a project manager for the first time.
        """
        first_assigned = not change or form.initial['project_manager'] is None

        if obj.project_manager and first_assigned:
            obj.project_manager_first_assigned_on = now()
            obj.project_manager_first_assigned_by = request.user

        super().save_model(request, obj, form, change)


@admin.register(InvestmentProjectTeamMember)
@custom_add_permission(InvestmentProjectPermission.change_all)
@custom_change_permission(InvestmentProjectPermission.change_all)
@custom_delete_permission(InvestmentProjectPermission.change_all)
class InvestmentProjectTeamMemberAdmin(VersionAdmin):
    """Investment project team member admin."""

    raw_id_fields = (
        'investment_project',
        'adviser',
    )


admin.site.register(Involvement, ReadOnlyMetadataAdmin)

admin.site.register(LikelihoodToLand, OrderedMetadataAdmin)

admin.site.register(
    (
        InvestmentDeliveryPartner,
        InvestorType,
        ProjectManagerRequestStatus,
        SpecificProgramme,
    ),
    DisableableMetadataAdmin,
)
