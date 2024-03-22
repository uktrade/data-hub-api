from datahub.export_win import models
from datahub.metadata.registry import registry
from datahub.metadata.serializers import (
    HQTeamRegionOrPostSerializer, HVCSerializer,
)

registry.register(
    metadata_id='team-type',
    model=models.TeamType,
)

registry.register(
    filterset_fields=['team_type'],
    metadata_id='hq-team-region-or-post',
    model=models.HQTeamRegionOrPost,
    queryset=models.HQTeamRegionOrPost.objects.select_related(
        'team_type',
    ),
    serializer=HQTeamRegionOrPostSerializer,
)

registry.register(
    metadata_id='win-type',
    model=models.WinType,
)

registry.register(
    metadata_id='winukregion',
    model=models.WinUKRegion,
)

registry.register(
    metadata_id='business-potential',
    model=models.BusinessPotential,
)

registry.register(
    metadata_id='support-type',
    model=models.SupportType,
)

registry.register(
    metadata_id='expected-value-relation',
    model=models.ExpectedValueRelation,
)

registry.register(
    metadata_id='experience-categories',
    model=models.ExperienceCategories,
)

registry.register(
    metadata_id='breakdown-type',
    model=models.BreakdownType,
)

registry.register(
    metadata_id='rating',
    model=models.Rating,
)

registry.register(
    metadata_id='experience',
    model=models.Experience,
)

registry.register(
    metadata_id='marketing-source',
    model=models.MarketingSource,
)

registry.register(
    metadata_id='without-our-support',
    model=models.WithoutOurSupport,
)

registry.register(
    metadata_id='hvo-programmes',
    model=models.HVOProgrammes,
)

registry.register(
    metadata_id='associated-programme',
    model=models.AssociatedProgramme,
)

registry.register(
    filterset_fields=['financial_year'],
    metadata_id='hvc',
    model=models.HVC,
    serializer=HVCSerializer,
)
