from django.contrib import admin

from datahub.company.models import (
    ExportExperience,
    ExportExperienceCategory,
    ExportYear,
    OneListTier,
)
from datahub.metadata.admin import (
    DisableableMetadataAdmin,
    OrderedMetadataAdmin,
    ReadOnlyMetadataAdmin,
)


admin.site.register(ExportExperienceCategory, DisableableMetadataAdmin)
admin.site.register(OneListTier, ReadOnlyMetadataAdmin)

admin.site.register(ExportExperience, OrderedMetadataAdmin)
admin.site.register(ExportYear, OrderedMetadataAdmin)
