from datahub.metadata.registry import registry
from .models import EvidenceTag


registry.register(
    metadata_id='evidence-tag',
    model=EvidenceTag,
)
