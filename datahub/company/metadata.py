from datahub.company.models import ExportExperienceCategory, OneListTier
from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry


class InteractionFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/export_experience_categories.yaml',
    ]


registry.register(
    metadata_id='export-experience-category',
    model=ExportExperienceCategory,
)

registry.register(
    metadata_id='one-list-tier',
    model=OneListTier,
    queryset=OneListTier.objects.all(),
)
