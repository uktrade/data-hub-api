from django.contrib import admin

from datahub.company.models import ExportExperienceCategory, OneListTier
from datahub.metadata.admin import DisableableMetadataAdmin, ReadOnlyMetadataAdmin


admin.site.register(ExportExperienceCategory, DisableableMetadataAdmin)
admin.site.register(OneListTier, ReadOnlyMetadataAdmin)
