from django.contrib import admin

from datahub.investment_lead.models import EYBLead


class EYBLeadAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'created_on',
        'modified_on',
        'company',
    ]
    readonly_fields = [
        'id',
        'created_on',
        'modified_on',
        'investment_projects',
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
                    'sector_sub',
                    'intent',
                    'intent_other',
                    'location',
                    'location_none',
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
                    'company_location',
                    'full_name',
                    'role',
                    'email',
                    'telephone_number',
                    'agree_terms',
                    'agree_info_email',
                    'landing_timeframe',
                    'company_website',
                ],
            },
        ),
        (
            'Company Information',
            {
                'fields': [
                    'company',
                    'duns_number',
                    'address_1',
                    'address_2',
                    'address_town',
                    'address_county',
                    'address_area',
                    'address_country',
                    'address_postcode',
                ],
            },
        ),
        (
            'Investment Projects',
            {
                'fields': [
                    'investment_projects',
                ]
            }
        ),
    ]


admin.site.register(EYBLead, EYBLeadAdmin)
