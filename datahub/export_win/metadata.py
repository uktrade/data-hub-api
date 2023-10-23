from datahub.export_win import models
from datahub.metadata.registry import registry
from datahub.metadata.serializers import (
    HQTeamRegionOrPostSerializer,
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
