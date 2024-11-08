from django.contrib import admin

from datahub.investment_lead.models import EYBLead


class EYBLeadAdmin(admin.ModelAdmin):
    search_fields = [
        'triage_hashed_uuid',
        'user_hashed_uuid',
        'company_name',
        'id',
    ]
    list_display = [
        'id',
        'created_on',
        'modified_on',
        'company_name',
    ]
    raw_id_fields = [
        'company',
        'investment_projects',
    ]
    readonly_fields = [
        'id',
        'created_on',
        'modified_on',
    ]
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'id',
                    'created_on',
                    'modified_on',
                ],
            },
        ),
        (
            'Triage Information',
            {
                'fields': [
                    'triage_hashed_uuid',
                    'triage_created',
                    'triage_modified',
                    'sector',
                    'intent',
                    'intent_other',
                    'proposed_investment_region',
                    'proposed_investment_city',
                    'proposed_investment_location_none',
                    'hiring',
                    'spend',
                    'spend_other',
                    'is_high_value',
                ],
            },
        ),
        (
            'User Information',
            {
                'fields': [
                    'user_hashed_uuid',
                    'user_created',
                    'user_modified',
                    'company_name',
                    'duns_number',
                    'address_1',
                    'address_2',
                    'address_town',
                    'address_county',
                    'address_country',
                    'address_postcode',
                    'company_website',
                    'company',
                    'full_name',
                    'role',
                    'email',
                    'telephone_number',
                    'agree_terms',
                    'agree_info_email',
                    'landing_timeframe',
                ],
            },
        ),
        (
            'Marketing Information',
            {
                'fields': [
                    'marketing_hashed_uuid',
                    'utm_name',
                    'utm_source',
                    'utm_medium',
                    'utm_content',
                ],
            },
        ),
        (
            'Investment Projects',
            {
                'fields': [
                    'investment_projects',
                ],
            },
        ),
    ]


admin.site.register(EYBLead, EYBLeadAdmin)
