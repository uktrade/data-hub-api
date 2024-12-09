from django.contrib import admin

from datahub.ingest.models import IngestedObject


class IngestedObjectAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'created',
        'object_key',
        'object_created',
    ]
    list_display = [
        'id',
        'created',
        'object_key',
        'object_created',
    ]
    readonly_fields = [
        'id',
        'created',
    ]
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'id',
                    'created',
                ],
            },
        ),
        (
            'Object Details',
            {
                'fields': [
                    'object_key',
                    'object_created',
                ],
            },
        ),
    ]


admin.site.register(IngestedObject, IngestedObjectAdmin)
