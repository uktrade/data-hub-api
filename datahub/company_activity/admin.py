from django.contrib import admin

from datahub.company_activity.models import IngestedFile


class IngestedFileAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'created_on',
        'filepath',
        'file_created',
    ]
    list_display = [
        'id',
        'created_on',
        'filepath',
        'file_created',
    ]
    readonly_fields = [
        'id',
        'created_on',
    ]
    fieldsets = [
        (
            None,
            {
                'fields': [
                    'id',
                    'created_on',
                    'filepath',
                    'file_created',
                ],
            },
        ),
    ]


admin.site.register(IngestedFile, IngestedFileAdmin)
