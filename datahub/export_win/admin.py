import reversion
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Concat
from django.forms import BaseInlineFormSet, ModelForm, ValidationError
from django.urls import reverse
from reversion.admin import VersionAdmin

from datahub.core.admin import BaseModelAdminMixin, EXPORT_WIN_GROUP_NAME

from datahub.export_win.models import (
    AnonymousWin,
    Breakdown,
    CustomerResponse,
    DeletedWin,
    Win,
    WinAdviser)

from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
    notify_export_win_email_by_rq_email,
    update_customer_response_token_for_email_notification_id,
)


class BaseTabularInline(admin.TabularInline):
    """Baseline tabular in line."""

    extra = 0
    can_delete = False
    exclude = ('id',)


class RequiredInLineFormSet(BaseInlineFormSet):
    """Generates an inline formset that is required"""

    def clean(self):
        """Clean and sanitise form array"""
        super().clean()
        if any(self.errors):
            return
        if not any(
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ):
            raise ValidationError('You must specify at least one record.')


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
    formset = RequiredInLineFormSet

    fields = ('id', 'type', 'year', 'value')
    verbose_name_plural = 'Breakdowns'


class AdvisorInlineForm(ModelForm):
    """Advisor inline form."""

    class Meta:
        model = WinAdviser
        fields = '__all__'
        labels = {
            'adviser': 'Contributing Adviser',
        }

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
        'responded_on',
        'lead_officer_email_notification_id',
        'lead_officer_email_delivery_status',
        'lead_officer_email_sent_on',
    )

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'id' in fields and 'responded_on' in fields:
            fields = list(fields)
            fields.remove('responded_on')
            id_index = fields.index('id')
            fields.insert(id_index + 1, 'responded_on')
        return fields


class WinAdminForm(ModelForm):
    """Admin for Wins."""

    class Meta:
        model = Win
        fields = '__all__'
        labels = {
            'adviser': 'Creator',
            'company_contacts': 'Contact names',
            'total_expected_odi_value': 'Total expected ODI value',
        }

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
    get_contact_names.short_description = 'Contact names'

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
        labels = {
            'adviser': 'Creator',
            'company_contacts': 'Contact names',
            'total_expected_odi_value': 'Total expected ODI value',
        }

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


class AnonymousWinAdminForm(ModelForm):
    """Admin form for Anonymous Wins."""

    class Meta:
        model = AnonymousWin
        fields = '__all__'
        labels = {
            'adviser': 'Creator',
            'company': 'Company (leave blank for an anonymous win)',
            'company_contacts': 'Contact names (leave blank for an anonymous win)',
            'total_expected_odi_value': 'Total expected ODI value',
            'customer_email_address': 'Company email',
            'name_of_customer': 'Overseas customer (leave blank for an anonymous win)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name_of_customer'].required = False

        optional_legacy_fields = {
            'cdms_reference': 'Data Hub (Companies House) or CDMS reference number',
            'customer_email_address': 'Contact email',
            'customer_job_title': 'Job title',
            'line_manager_name': 'Line manager',
            'lead_officer_email_address': 'Lead officer email address',
            'other_official_email_address': 'Secondary email address',
        }

        for field_name, label in optional_legacy_fields.items():
            if field_name in self.fields:
                self.fields[field_name].required = False
                self.fields[field_name].label = f'{label} (legacy)'

        mandatory_fields_for_anonymous_wins = {
            'lead_officer': 'Lead officer',
            'export_experience': 'Export experience',
            'business_potential': 'Medium-sized and high potential companies',
            'customer_location': 'HQ location',
            'sector': 'Sector',
        }

        for field_name, label in mandatory_fields_for_anonymous_wins.items():
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].label = f'{label}'


@admin.register(AnonymousWin)
class AnonymousWinAdmin(WinAdmin):
    """Admin for Anonymous Wins."""

    form = AnonymousWinAdminForm
    inlines = (BreakdownInline, CustomerResponseInline, AdvisorInline)

    def save_model(self, request, obj, form, change):
        with transaction.atomic(), reversion.create_revision():
            if not change:
                obj.is_personally_confirmed = True
                obj.is_line_manager_confirmed = True
                obj.is_anonymous_win = True
                obj.adviser = request.user
            super().save_model(request, obj, form, change)

            # Customer response will be created upon wins being saved
            if not change:
                customer_response = CustomerResponse.objects.create(win=obj)
                self.notify_anonymous_wins_adviser_as_contact(request.user, customer_response)

            reversion.set_comment('Anonymous Win created')

    def get_queryset(self, request):
        """Return win queryset only for anonymous win."""
        return self.model.anonymous_objects.anonymous_win()

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        """Set the desired user group to access view anonymous win"""
        if (
            request.user.is_superuser
            or request.user.groups.filter(name=EXPORT_WIN_GROUP_NAME).exists()
        ):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def notify_anonymous_wins_adviser_as_contact(self, adviser, customer_response):
        """Notify anonymous wins adviser as contact"""
        token = create_token_for_contact(
            None,
            customer_response,
            adviser,
        )
        context = get_all_fields_for_client_email_receipt(
            token,
            customer_response,
        )
        template_id = settings.EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID
        notify_export_win_email_by_rq_email(
            adviser.contact_email,
            template_id,
            context,
            update_customer_response_token_for_email_notification_id,
            token.id,
        )


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
