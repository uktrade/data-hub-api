from functools import partial

from django import forms
from django.contrib import admin
from django.contrib.postgres.forms.array import SplitArrayField
from django.db import models
from django.forms.fields import CharField
from django.urls import path
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin

from datahub.company.admin.archiving.unarchive import unarchive_company
from datahub.company.admin.merge.step_1 import merge_select_other_company
from datahub.company.admin.merge.step_2 import select_primary_company
from datahub.company.admin.merge.step_3 import confirm_merge
from datahub.company.admin.update_from_dnb import update_from_dnb
from datahub.company.models import Company, OneListCoreTeamMember
from datahub.core.admin import BaseModelAdminMixin, get_change_link
from datahub.core.templatetags.datahub_extras import admin_change_link


class OneListCoreTeamMemberInline(admin.TabularInline):
    """Inline admin for OneListCoreTeamMember"""

    model = OneListCoreTeamMember
    fields = ('id', 'adviser')
    extra = 1
    formfield_overrides = {
        models.UUIDField: {'widget': forms.HiddenInput},
    }
    raw_id_fields = (
        'adviser',
    )


class CompanyAdminForm(forms.ModelForm):
    """Admin form for Company."""

    TRADING_NAMES_DEFAULT_FIELD_SIZE = 5

    trading_names = SplitArrayField(
        base_field=CharField(max_length=255, required=False),
        size=TRADING_NAMES_DEFAULT_FIELD_SIZE,
        required=False,
        remove_trailing_nulls=True,
        help_text=Company._meta.get_field('trading_names').help_text,
    )

    def __init__(self, *args, **kwargs):
        """Initialises the form."""
        super().__init__(*args, **kwargs)
        self.set_trading_names_field_size()

    def set_trading_names_field_size(self):
        """
        Sets the size of the form field trading_names using the following logic:

        given TRADING_NAMES_DEFAULT_FIELD_SIZE as default size
        the actual array field size for the specific self.instance is:
            n = max(
                TRADING_NAMES_DEFAULT_FIELD_SIZE,
                (len of instance.trading_names + 1)
            )

        This creates n separate form fields in the django admin allowing the user to
        add up to n trading names. If more are required, saving and refreshing the
        page will add one more form field.
        """
        field = self.fields['trading_names']
        trading_names = self.instance.trading_names or []

        new_field_size = max(
            field.size,
            (len(trading_names) + 1),
        )
        field.size = new_field_size
        field.widget.size = new_field_size

    class Meta:
        model = Company
        exclude = []  # fields are specified in CompanyAdmin


@admin.register(Company)
class CompanyAdmin(BaseModelAdminMixin, VersionAdmin):
    """Company admin."""

    form = CompanyAdminForm
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'created',
                    'modified',
                    'name',
                    'trading_names',
                    'company_number',
                    'vat_number',
                    'duns_number',
                    'description',
                    'website',
                    'business_type',
                    'sector',
                    'uk_region',
                    'employee_range',
                    'number_of_employees',
                    'is_number_of_employees_estimated',
                    'turnover_range',
                    'turnover',
                    'is_turnover_estimated',
                    'one_list_tier',
                    'one_list_account_owner',
                ),
            },
        ),
        (
            'HIERARCHY',
            {
                'fields': (
                    'headquarter_type',
                    'global_headquarters',
                ),
            },
        ),
        (
            'ADDRESS',
            {
                'description': (
                    'The address fields are in the process of being migrated. '
                    'Address is the main location for this business '
                    '(could be trading, registered or a different address) '
                    'whilst registered address is the official address '
                    '(e.g. from companies house).'
                ),
                'fields': (
                    'address_1',
                    'address_2',
                    'address_town',
                    'address_county',
                    'address_postcode',
                    'address_country',

                    'registered_address_1',
                    'registered_address_2',
                    'registered_address_town',
                    'registered_address_county',
                    'registered_address_postcode',
                    'registered_address_country',
                ),
            },
        ),
        (
            'EXPORT',
            {
                'fields': (
                    'export_experience_category',
                    'export_to_countries',
                    'future_interest_countries',
                ),
            },
        ),
        (
            'LEGACY FIELDS',
            {
                'fields': (
                    'reference_code',
                    'archived_documents_url_path',
                ),
            },
        ),
        (
            'ARCHIVING AND MERGING',
            {
                'fields': (
                    'archived',
                    'archived_on',
                    'archived_by',
                    'archived_reason',
                    'transferred_to_display',
                    'transferred_by',
                    'transferred_on',
                    'transferred_from_display',
                ),
            },
        ),
    )
    search_fields = (
        'name',
        'id',
        'company_number',
        'duns_number',
    )
    raw_id_fields = (
        'global_headquarters',
        'one_list_account_owner',
        'archived_by',
    )
    readonly_fields = (
        'id',
        'created',
        'modified',
        'archived_documents_url_path',
        'reference_code',
        'transferred_to_display',
        'transferred_by',
        'transferred_on',
        'transferred_from_display',
    )
    list_display = (
        'name',
        'registered_address_country',
    )
    list_filter = (
        'dnb_modified_on',
    )
    inlines = (
        OneListCoreTeamMemberInline,
    )
    # Help text for read-only method fields
    extra_help_texts = {
        'transferred_to_display':
            Company._meta.get_field('transferred_to').help_text,
        'transferred_from_display':
            'Other records whose data has been transferred to this record.',
    }

    def get_form(self, request, obj=None, **kwargs):
        """
        Gets the model form used for add and change views.

        Overridden here to add help text for read-only method fields.
        """
        return super().get_form(request, obj, help_texts=self.extra_help_texts, **kwargs)

    def get_urls(self):
        """Gets the URLs for this model."""
        model_meta = self.model._meta

        return [
            path(
                'merge/step-1-select-other-company/',
                self.admin_site.admin_view(partial(merge_select_other_company, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-select-other-company',
            ),
            path(
                'merge/step-2-select-primary-company/',
                self.admin_site.admin_view(partial(select_primary_company, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-select-primary-company',
            ),
            path(
                'merge/step-3-confirm/',
                self.admin_site.admin_view(partial(confirm_merge, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_merge-confirm',
            ),
            path(
                'archiving/unarchive-company/',
                self.admin_site.admin_view(partial(unarchive_company, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_unarchive-company',
            ),
            path(
                '<path:object_id>/update-from-dnb/',
                self.admin_site.admin_view(partial(update_from_dnb, self)),
                name=f'{model_meta.app_label}_'
                     f'{model_meta.model_name}_update-from-dnb',
            ),
            *super().get_urls(),
        ]

    def transferred_to_display(self, obj):
        """Link to the company that data for this company has been transferred to."""
        return get_change_link(obj.transferred_to)

    transferred_to_display.short_description = 'transferred to'

    def transferred_from_display(self, obj):
        """List of other companies that have had their data transferred to this company."""
        return format_html_join(
            mark_safe('<br>'),
            '{0} ({1})',
            (
                (admin_change_link(company), company.transfer_reason.lower())
                for company in obj.transferred_from.all()
            ),
        )

    transferred_from_display.short_description = 'Transferred from'
