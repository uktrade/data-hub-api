from django.contrib import admin

from datahub.eyb.models import EYBLead


class EYBLeadAdmin(admin.ModelAdmin):
    list_display = (
        # EYB Triage data
        'triage_id',
        'triage_hashed_uuid',
        'triage_created',
        'triage_modified',
        'sector',
        'sector_sub',
        'intent',
        'intent_other',
        'location',
        'location',
        'location_none',
        'hiring',
        'spend',
        'spend_other',
        'is_high_value',

        # EYB User data
        'user_id',
        'user_hashed_uuid',
        'user_created',
        'user_modified',
        'company_name',
        'company_location',
        'full_name',
        'role',
        'email',
        'telephone_number',
        'agree_terms',
        'agree_info_email',
        'landing_timeframe',
        'company_website',
    )


admin.site.register(EYBLead, EYBLeadAdmin)
