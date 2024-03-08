from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.forms import ModelForm
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin
from datahub.export_win.models import Breakdown, CustomerResponse, DeletedWin, Win, WinAdviser


class BaseTabularInLine(admin.TabularInline):
    """Baseline tabular in line."""

    extra = 0
    can_delete = False


class BreakdownInLine(BaseTabularInLine):
    """Breakdown model."""

    model = Breakdown
    min_num = 1
    extra = 0

    fields = ('type', 'year', 'value')
    verbose_name_plural = 'Breakdowns'


class AdvisorInLineForm(ModelForm):
    """Advisor inline form."""

    class Meta:
        model = WinAdviser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['name'].required = False
            self.fields['team_type'].required = False
            self.fields['hq_team'].required = False


class AdvisorInLine(BaseTabularInLine):
    """Advisor model."""

    model = WinAdviser
    form = AdvisorInLineForm
    min_num = 1
    extra = 0

    fields = ('name', 'team_type', 'hq_team', 'location')
    verbose_name_plural = 'Contributing Advisors'


class BaseStackedInLine(admin.StackedInline):
    """Base stacked in line."""

    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)
    extra = 0
    can_delete = False


class CustomerResponseInLineForm(ModelForm):
    """Customer response inline form."""

    class Meta:
        model = CustomerResponse
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['name'].required = False


class CustomerResponseInLine(BaseStackedInLine):
    """Customer response in line."""

    model = CustomerResponse
    form = CustomerResponseInLineForm

    def has_add_permission(self, request, obj=None):
        return False


class WinAdminForm(ModelForm):
    """Win admin form."""

    class Meta:
        model = Win
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['cdms_reference'].required = False
            self.fields['customer_email_address'].required = False
            self.fields['customer_job_title'].required = False
            self.fields['line_manager_name'].required = False
            self.fields['lead_officer_email_address'].required = False
            self.fields['other_official_email_address'].required = False


@admin.register(Win)
class WinAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin for Wins."""

    form = WinAdminForm
    actions = ('soft_delete',)
    list_display = (
        'id',
        'get_adviser',
        'get_company',
        'get_contact_names',
        'lead_officer',
        'country',
        'sector',
        'get_date_confirmed',
        'created_on',
    )
    list_filter = (
        ('created_on', DateFieldListFilter),
    )
    readonly_fields = (
        'id',
        'created_on',
        'modified_on',
    )
    search_fields = (
        'adviser__name',
        'company__name',
        'pk',
    )
    fieldsets = (
        ('Overview', {'fields': (
            'id',
            'adviser',
            'company',
            'company_contacts',
            'created_on',
            # 'modified_on', TODO: Added later
            'audit',
            'total_expected_export_value',
            'total_expected_non_export_value',
            'total_expected_odi_value',

        )}),
        ('Win details', {'fields': (
            'country',
            'date',
            'description',
            'name_of_customer',
            'goods_vs_services',
            'name_of_export',
            'sector',
            'hvc',
        )}),
        ('Customer details', {'fields': (
            'cdms_reference',  # Legacy field
            'customer_email_address',  # Legacy field
            'customer_job_title',  # Legacy field
            'customer_location',
            'business_potential',
            'export_experience',
        )}),
        ('DBT Officer', {'fields': (
            'lead_officer',
            'team_type',
            'hq_team',
            'line_manager_name',  # Legacy field
            'lead_officer_email_address',  # Legacy field
            'other_official_email_address',  # Legacy field
        )}),
        ('DBT Support', {'fields': (
            'type_of_support',
            'associated_programme',
        )}),
    )
    inlines = (
        BreakdownInLine,
        CustomerResponseInLine,
        AdvisorInLine,
    )

    def get_adviser(self, obj):
        """Return adviser as user with email."""
        return f'{obj.adviser} <{obj.adviser.email}>'
    get_adviser.short_description = 'User'

    def get_company(self, obj):
        """Return company name."""
        return obj.company
    get_company.short_description = 'Organisation or Company name'

    def get_date_confirmed(self, obj):
        """Return wins being confirmed."""
        return obj.customer_response.responded_on
    get_date_confirmed.short_description = 'Date win confirmed'

    def get_contact_names(self, obj):
        """Return a comma separated list of company contact names."""
        return ', '.join(contact.name for contact in obj.company_contacts.all())
    get_contact_names.short_description = 'Contact name'

    def get_actions(self, request):
        """Remove the delete selected action."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def soft_delete(self, request, queryset):
        """Soft delete action for django admin."""
        for win in queryset.all():
            win.is_deleted = True
            win.modified_by = request.user
            win.save()


@admin.register(DeletedWin)
class DeletedWinAdmin(WinAdmin):
    inlines = tuple()
    actions = ('undelete',)

    def undelete(self, request, queryset):
        for win in queryset.all():
            win.is_deleted = True
