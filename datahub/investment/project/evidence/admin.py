from django.contrib import admin

from datahub.investment.evidence.models import EvidenceTag
from datahub.metadata.admin import DisableableMetadataAdmin


@admin.register(EvidenceTag)
class EvidenceTagAdmin(DisableableMetadataAdmin):
    """Evidence Tag Admin."""
