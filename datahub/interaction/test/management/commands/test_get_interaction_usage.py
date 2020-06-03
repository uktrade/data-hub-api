import pytest
from django.core.management import call_command

from datahub.company.test.factories import AdviserFactory
from datahub.interaction.test.factories import ExportCountriesInteractionFactory
from datahub.metadata.test.factories import TeamFactory, TeamRoleFactory

pytestmark = pytest.mark.django_db


def test_get_interaction_usage_details(caplog):
    """
    Test get_interaction_usage command retrieves the interaction
    details as expected.
    """
    team_role = TeamRoleFactory(name='Role')
    team = TeamFactory(name='Team', role=team_role)
    advisor = AdviserFactory(dit_team=team)
    ExportCountriesInteractionFactory(created_by=advisor)

    caplog.set_level('INFO')

    call_command('get_interaction_usage')

    expected_text = [
        '1 uses of new interaction journey',
        '1 countries added against 1',
        '1 teams used the new feature',
        "('Team', 'Role', 1)",
    ]

    for text in expected_text:
        assert text in caplog.text
