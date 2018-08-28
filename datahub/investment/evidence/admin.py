from django.contrib import admin

from datahub.metadata.admin import DisableableMetadataAdmin
from .models import EvidenceTag


@admin.register(EvidenceTag)
class EvidenceTagAdmin(DisableableMetadataAdmin):
    """Evidence Tag Admin."""
