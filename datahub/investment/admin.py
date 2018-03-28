"""Admin registration for investment models."""
import csv

from django.contrib import admin
from django.http import HttpResponse
from django.template.response import TemplateResponse
from reversion.admin import VersionAdmin

from datahub.core.admin import (
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
)
from datahub.investment.models import (
    InvestmentDeliveryPartner,
    InvestmentProject,
    InvestmentProjectPermission,
    InvestmentProjectSPIReportConfiguration,
    InvestmentProjectTeamMember,
    InvestorType,
    Involvement,
    IProjectDocument,
    SpecificProgramme,
)
from datahub.investment.report import generate_spi_report, get_spi_report_fieldnames
from datahub.metadata.admin import DisableableMetadataAdmin


@admin.register(InvestmentProject)
@custom_change_permission(InvestmentProjectPermission.change_all)
class InvestmentProjectAdmin(VersionAdmin):
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
    list_display = (
        'name',
        'investor_company',
        'stage',
    )


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


admin.site.register((
    InvestmentDeliveryPartner,
    InvestorType,
    Involvement,
    SpecificProgramme,
), DisableableMetadataAdmin)


@admin.register(
    InvestmentProjectSPIReportConfiguration
)
class InvestmentProjectSPIReportConfigurationAdmin(admin.ModelAdmin):
    """Investment Project SPI Report Configuration Admin."""

    fields = (
        'active_stage',
        'verify_win_stage',
        'after_care_offered',
        'project_manager_assigned',
        'client_proposal',
    )

    actions = ('create_spi_report',)

    def has_add_permission(self, request):
        """Disallow adding new configuration records if one already exists."""
        has_permission = super().has_add_permission(request)
        if has_permission:
            if not InvestmentProjectSPIReportConfiguration.objects.exists():
                return True
        return False

    def add_view(self, request, form_url='', extra_context=None):
        """Remove unnecessary buttons."""
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        # key below requires modification to "submit_row" templatetag, which is included in
        # core/admin.py
        extra_context['show_save_and_add_another'] = False
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def create_spi_report(self, request, queryset):
        """Create SPI report action."""
        if request.POST.get('create') == 'yes':
            self.message_user(request, 'Created')

            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            report = generate_spi_report(month, year)

            response = HttpResponse(content_type='text/csv')
            filename = f'attachment; filename="Investment Projects SPI {month} {year}.csv"'
            response['Content-Disposition'] = filename
            fieldnames = get_spi_report_fieldnames()
            dw = csv.DictWriter(
                response,
                delimiter=',',
                fieldnames=fieldnames.keys()
            )
            dw.writer.writerow(fieldnames.values())

            for row in report:
                dw.writerow(row)

            return response

        context = dict(
            self.admin_site.each_context(request),
            title='Create SPI Report',
            action=self.create_spi_report.__name__,
            action_message='Create SPI Report',
            action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
            opts=self.model._meta,
            queryset=queryset,
            media=self.media,
        )

        return TemplateResponse(request, 'admin/action_create_spi_report.html', context)

    create_spi_report.short_description = 'Create spi report'
