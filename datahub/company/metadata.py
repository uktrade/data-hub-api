from datahub.company.models import (
    ExportExperience,
    ExportExperienceCategory,
    ExportYear,
    OneListTier,
)
from datahub.metadata.fixtures import Fixture
from datahub.metadata.registry import registry


class InteractionFixtures(Fixture):
    """Metadata fixtures (for the loadinitialmetadata command)."""

    files = [
        'fixtures/export_experience_categories.yaml',
        'fixtures/company_export_experience.yaml',
        'fixtures/export_years.yaml',
    ]


registry.register(
    metadata_id='export-experience-category',
    model=ExportExperienceCategory,
)

registry.register(
    metadata_id='one-list-tier',
    model=OneListTier,
)

registry.register(
    metadata_id='export-experience',
    model=ExportExperience,
)

registry.register(
    metadata_id='export-years',
    model=ExportYear,
)
