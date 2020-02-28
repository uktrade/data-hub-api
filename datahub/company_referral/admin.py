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
    raw_id_fields = (
        'company',
        'completed_by',
        'contact',
        'interaction',
        'recipient',
    )
    readonly_fields = (
        'id',
        'created',
        'modified',
    )
    list_display = (
        'subject',
        'company',
        'status',
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
