import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.export_win.constants import TeamType as TeamTypeConstant
from datahub.export_win.models import HQTeamRegionOrPost, TeamType

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'team_type_id, results_length',
    (
        (
            TeamTypeConstant.team.value.id,
            73,
        ),
        (
            TeamTypeConstant.investment.value.id,
            56,
        ),
        (
            TeamTypeConstant.dso.value.id,
            30,
        ),
        (
            TeamTypeConstant.obn.value.id,
            41,
        ),
        (
            TeamTypeConstant.other.value.id,
            13,
        ),
        (
            TeamTypeConstant.itt.value.id,
            23,
        ),
        (
            TeamTypeConstant.post.value.id,
            239,
        ),
        (
            TeamTypeConstant.tcp.value.id,
            73,
        ),
    ),
)
def test_hq_team_region_or_post(metadata_client, team_type_id, results_length):
    """Test the HQTeamRegionOrPost view when filtered by team type"""
    team = TeamType.objects.get(id=team_type_id)
    hq_team_region_or_post = HQTeamRegionOrPost.objects.filter(
        team_type=team,
    ).first()

    url = reverse(viewname='api-v4:metadata:hq-team-region-or-post')
    response = metadata_client.get(url, params={'team_type': team.id})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()

    assert len(results) == results_length
    assert results[0] == {
        'id': str(hq_team_region_or_post.pk),
        'name': hq_team_region_or_post.name,
        'disabled_on': None,
        'team_type': {
            'name': team.name,
            'id': str(team.pk),
        },
    }
