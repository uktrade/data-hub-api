from django.contrib import admin

from datahub.company_referral.models import CompanyReferral
from datahub.core.admin import BaseModelAdminMixin


@admin.register(CompanyReferral)
class CompanyReferralAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Company referral admin."""

    search_fields = (
        'pk',
        'company__pk',
        'company__name',
    )
    ordering = (
        '-created_on',
    )
    raw_id_fields = (
        'company',
        'contact',
        'recipient',
        'completed_by',
    )
    readonly_fields = (
        'created',
        'modified',
    )
    list_display = (
        'company',
        'subject',
        'created_on',
    )
    list_select_related = (
        'company',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
