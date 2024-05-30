import reversion
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.db.models import Value
from django.db.models.functions import Concat
from django.forms import ModelForm
from django.urls import reverse
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, EXPORT_WIN_GROUP_NAME

from datahub.export_win.models import (
    Breakdown,
    CustomerResponse,
    DeletedWin,
    Win,
    WinAdviser)


class BaseTabularInline(admin.TabularInline):
    """Baseline tabular in line."""

    extra = 0
    can_delete = False
    exclude = ('id',)


class BreakdownInlineForm(ModelForm):
    """Breakdown inline form."""

    class Meta:
        model = Breakdown
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BreakdownInline(BaseTabularInline):
    """Breakdown model."""

    model = Breakdown
    form = BreakdownInlineForm

    fields = ('id', 'type', 'year', 'value')
    verbose_name_plural = 'Breakdowns'


class AdvisorInlineForm(ModelForm):
    """Advisor inline form."""

    class Meta:
        model = WinAdviser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AdvisorInline(BaseTabularInline):
    """Advisor model."""

    autocomplete_fields = (
        'adviser',
    )
    can_delete = True
    model = WinAdviser
    form = AdvisorInlineForm
    fields = ('id', 'adviser', 'team_type', 'hq_team', 'location')
    verbose_name_plural = 'Contributing Advisers'


class BaseStackedInline(admin.StackedInline):
    """Base stacked in line."""

    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)
    extra = 0
    can_delete = False
    exclude = ('created_by', 'modified_by')


class CustomerResponseInlineForm(ModelForm):
    """
    Customer Response in line form.
    Field name is not required and field id should be read-only
    """

    class Meta:
        model = CustomerResponse
        fields = '__all__'

    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)

        instance = getattr(self, 'instance', None)
        is_instance_and_pk_exist = getattr(instance, 'pk', None) is not None
        self.fields['name'].required = not is_instance_and_pk_exist
        self.fields['id'].widget.attrs['readonly'] = is_instance_and_pk_exist


class CustomerResponseInline(BaseStackedInline):
    """Customer response in line."""

    model = CustomerResponse
    form = CustomerResponseInlineForm
    readonly_fields = (
        'lead_officer_email_notification_id',
        'lead_officer_email_delivery_status',
        'lead_officer_email_sent_on',
    )


class WinAdminForm(ModelForm):
    """Admin for Wins."""

    class Meta:
        model = Win
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['audit'].required = True

        legacy_fields = {
            'cdms_reference': 'Data Hub (Companies House) or CDMS reference number',
            'customer_email_address': 'Contact email',
            'customer_job_title': 'Job title',
            'line_manager_name': 'Line manager',
            'lead_officer_email_address': 'Lead officer email address',
            'other_official_email_address': 'Secondary email address',
        }

        for field_name, label in legacy_fields.items():
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].label = f'{label} (legacy)'


@admin.register(Win)
class WinAdmin(BaseModelAdminMixin, VersionAdmin):
    """Admin for Wins."""

    form = WinAdminForm
    actions = ('soft_delete',)
    list_per_page = 10
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
    autocomplete_fields = (
        'company',
        'company_contacts',
        'lead_officer',
        'team_members',
    )
    readonly_fields = (
        'id',
        'adviser',
        'created_on',
        'modified_on',
        'total_expected_export_value',
        'total_expected_non_export_value',
        'total_expected_odi_value',
    )
    search_fields = (
        '=id',
        'computed_adviser_name',
        # legacy field
        'adviser_name',
        '=company__pk',
        'lead_officer_adviser_name',
        # legacy field
        'lead_officer_name',
        'company__name',
        'country__name',
        'contact_name',
        'sector__segment',
        'customer_response__responded_on',
        'created_on',
    )
    fieldsets = (
        ('Overview', {'fields': (
            'id',
            'adviser',
            'company',
            'company_contacts',
            'created_on',
            'modified_on',
            'audit',
            'total_expected_export_value',
            'total_expected_non_export_value',
            ('total_expected_odi_value', 'Total expected ODI value'),
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
            'team_members',
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
    inlines = [
        BreakdownInline,
        CustomerResponseInline,
        AdvisorInline,
    ]

    def get_adviser(self, obj):
        """Return adviser as user with email."""
        return f'{obj.adviser} <{obj.adviser.email}>' if obj.adviser else \
            f'{obj.adviser_name} <{obj.adviser_email_address}>'

    get_adviser.short_description = 'Creator'

    def get_company(self, obj):
        """Return company name."""
        return obj.company
    get_company.short_description = 'Company name'

    def get_date_confirmed(self, obj):
        """Return wins being confirmed."""
        return obj.customer_response.responded_on
    get_date_confirmed.short_description = 'Date win confirmed'

    def get_contact_names(self, obj):
        """Return a comma separated list of company contact names."""
        return ', '.join(
            contact.name for contact in obj.company_contacts.all().order_by('last_name')
        )
    get_contact_names.short_description = 'Contact name'

    def get_actions(self, request):
        """Remove the delete selected action."""
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def soft_delete(self, request, queryset):
        """Soft delete action for django admin."""
        for win in queryset.all():
            with reversion.create_revision():
                win.is_deleted = True
                win.modified_by = request.user
                win.save()
                reversion.set_comment('Soft deleted')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                computed_adviser_name=Concat(
                    'adviser__first_name', Value(' '), 'adviser__last_name',
                ),
                lead_officer_adviser_name=Concat(
                    'lead_officer__first_name', Value(' '), 'lead_officer__last_name',
                ),
                contact_name=Concat(
                    'company_contacts__first_name', Value(' '), 'company_contacts__last_name',
                ),
            )

        return super().get_search_results(
            request,
            queryset,
            search_term,
        )


class WinSoftDeletedAdminForm(ModelForm):
    """Win soft deleted admin form"""

    class Meta:
        model = DeletedWin
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@admin.register(DeletedWin)
class DeletedWinAdmin(WinAdmin):
    """Admin for Deleted Wins."""

    form = WinSoftDeletedAdminForm
    inlines = (BreakdownInline, CustomerResponseInline, AdvisorInline)
    actions = ('undelete',)

    def get_queryset(self, request):
        """Return win queryset only for deleted win."""
        return self.model.objects.soft_deleted()

    def undelete(self, request, queryset):
        """Perform undelete action in django admin"""
        for win in queryset.all():
            with reversion.create_revision():
                win.is_deleted = False
                win.modified_by = request.user
                win.save()
                reversion.set_comment('Undeleted')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        """Set the desired user group to access view deleted win"""
        if (
            request.user.is_superuser
            or request.user.groups.filter(name=EXPORT_WIN_GROUP_NAME).exists()
        ):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WinAdviser)
class WinAdviserAdmin(BaseModelAdminMixin):
    """Admin for Win Adviser."""

    list_display = ('win', 'get_computed_adviser_name', 'team_type', 'hq_team', 'location')
    search_fields = ('win__id',)

    fieldsets = (
        ('Overview', {'fields': (
            'id',
            'win',
            'adviser',
            'team_type',
            'hq_team',
            'location',
        )}),
        ('Legacy Fields', {'fields': (
            'name',
            'legacy_id',
        )}),
    )

    autocomplete_fields = (
        'adviser',
    )

    def get_queryset(self, request):
        """Return winadviser queryset only for undeleted win."""
        queryset = super().get_queryset(request)
        return queryset.filter(win__is_deleted=False)

    def get_computed_adviser_name(self, obj):
        """Return computed adviser name."""
        return obj.adviser.name if obj.adviser else obj.name

    def delete_view(self, request, object_id, extra_context=None):
        """
        Redirect to the winadviser list view after successful deletion.
        """
        response = super().delete_view(request, object_id, extra_context=extra_context)
        if response.status_code == 302:  # Redirect status code
            response['Location'] = reverse('admin:export_win_winadviser_changelist')
        return response

    def has_change_permission(self, request, obj=None):
        return False

    get_computed_adviser_name.short_description = 'Contributing Adviser'

    WinAdviser._meta.verbose_name_plural = 'Advisers'
