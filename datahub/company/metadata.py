from datahub.company.models import ExportExperienceCategory
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
