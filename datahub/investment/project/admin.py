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
from datahub.investment.project.models import (
    GVAMultiplier,
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
        'gva_multiplier',
        'gross_value_added',
        'comments',
        'created',
        'modified',
        'financial_year_verbose',
        # Remove when migration to specific_programmes is complete
        'specific_programme',
        'specific_programmes',
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

    def financial_year_verbose(self, obj):
        """Financial year in YYYY-YY format, for example 2021-22."""
        return obj.financial_year_verbose
    financial_year_verbose.short_description = 'Financial year'

    def save_model(self, request, obj, form, change):
        """
        Populate who and when assigned a project manager for the first time.
        """
        first_assigned = not change or form.initial['project_manager'] is None

        if obj.project_manager and first_assigned:
            obj.project_manager_first_assigned_on = now()
            obj.project_manager_first_assigned_by = request.user

        if 'specific_programmes' in form.cleaned_data:
            specific_programmes = form.cleaned_data['specific_programmes']
            obj.specific_programme = specific_programmes[0] if specific_programmes else None

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


@admin.register(GVAMultiplier)
class GVAMultiplierAdmin(admin.ModelAdmin):
    """Investor profile admin."""

    list_display = ('sector', 'fdi_sic_grouping', 'financial_year', 'multiplier')
    search_fields = ('sector__segment', 'fdi_sic_grouping__name', 'financial_year', 'id')
    list_filter = ('fdi_sic_grouping', 'financial_year')

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'multiplier',
                    'financial_year',
                ),
            },
        ),
        (
            'SECTOR INFORMATION',
            {
                'fields': (
                    'sector',
                    'sector_classification_gva_multiplier',
                    'sector_classification_value_band',
                    'fdi_sic_grouping',
                ),
            },
        ),
        (
            'VALUE BANDS',
            {
                'fields': (
                    'value_band_a_minimum',
                    'value_band_b_minimum',
                    'value_band_c_minimum',
                    'value_band_d_minimum',
                    'value_band_e_minimum',
                ),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Get readonly fields. No fields can be updated via the admin due to be reference data."""
        if obj:
            return [
                'id',
                'multiplier',
                'financial_year',
                'sector',
                'sector_classification_gva_multiplier',
                'sector_classification_value_band',
                'value_band_a_minimum',
                'value_band_b_minimum',
                'value_band_c_minimum',
                'value_band_d_minimum',
                'value_band_e_minimum',
                'fdi_sic_grouping',
            ]
        else:
            return ['id']


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
