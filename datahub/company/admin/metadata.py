from django.contrib import admin

from datahub.company.models import ExportExperienceCategory
from datahub.metadata.admin import DisableableMetadataAdmin


admin.site.register(ExportExperienceCategory, DisableableMetadataAdmin)
