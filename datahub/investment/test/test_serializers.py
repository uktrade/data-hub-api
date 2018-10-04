import pytest

from datahub.company.test.factories import AdviserFactory
from datahub.investment.serializers import (
    IProjectTeamMemberListSerializer, IProjectTeamMemberSerializer,
)
from .factories import InvestmentProjectFactory, InvestmentProjectTeamMemberFactory


pytestmark = pytest.mark.django_db


def test_team_member_list_update_remove_all():
    """Tests removing all team members."""
    project = InvestmentProjectFactory()

    team_members = InvestmentProjectTeamMemberFactory.create_batch(
        2, investment_project=project,
    )

    child_serializer = IProjectTeamMemberSerializer()
    serializer = IProjectTeamMemberListSerializer(child=child_serializer)

    assert serializer.update(team_members, []) == []
    assert project.team_members.count() == 0


def test_team_member_list_update_mixed_changes():
    """Tests making mixed changes to team members."""
    project = InvestmentProjectFactory()

    team_members = InvestmentProjectTeamMemberFactory.create_batch(
        2, investment_project=project, role='old role',
    )
    adviser = AdviserFactory()

    new_team_member_data = [
        {
            'investment_project': project,
            'adviser': team_members[1].adviser,
            'role': 'new role',
        },
        {
            'investment_project': project,
            'adviser': adviser,
            'role': 'new team member',
        },
    ]

    child_serializer = IProjectTeamMemberSerializer()
    serializer = IProjectTeamMemberListSerializer(child=child_serializer)

    updated_team_members = serializer.update(team_members, new_team_member_data)

    assert len(updated_team_members) == 2
    assert updated_team_members[0].adviser == new_team_member_data[0]['adviser']
    assert updated_team_members[0].role == new_team_member_data[0]['role']
    assert updated_team_members[1].adviser == new_team_member_data[1]['adviser']
    assert updated_team_members[1].role == new_team_member_data[1]['role']

    assert project.team_members.count() == 2


def test_team_member_list_update_change_only():
    """Tests updating existing team members."""
    project = InvestmentProjectFactory()

    team_members = InvestmentProjectTeamMemberFactory.create_batch(
        2, investment_project=project, role='old role',
    )

    new_team_member_data = [
        {
            'investment_project': project,
            'adviser': team_members[0].adviser,
            'role': 'new role',
        },
        {
            'investment_project': project,
            'adviser': team_members[1].adviser,
            'role': 'new role',
        },
    ]

    child_serializer = IProjectTeamMemberSerializer()
    serializer = IProjectTeamMemberListSerializer(child=child_serializer)

    updated_team_members = serializer.update(team_members, new_team_member_data)

    assert len(updated_team_members) == 2
    assert updated_team_members[0].adviser == new_team_member_data[0]['adviser']
    assert updated_team_members[0].role == new_team_member_data[0]['role']
    assert updated_team_members[1].adviser == new_team_member_data[1]['adviser']
    assert updated_team_members[1].role == new_team_member_data[1]['role']

    assert project.team_members.count() == 2


def test_team_member_list_update_add_only():
    """Tests updating adding team members when none previously existed."""
    project = InvestmentProjectFactory()

    new_team_member_data = [
        {
            'investment_project': project,
            'adviser': AdviserFactory(),
            'role': 'new role',
        },
        {
            'investment_project': project,
            'adviser': AdviserFactory(),
            'role': 'new team member',
        },
    ]

    child_serializer = IProjectTeamMemberSerializer()
    serializer = IProjectTeamMemberListSerializer(child=child_serializer)

    updated_team_members = serializer.update([], new_team_member_data)

    assert updated_team_members[0].adviser == new_team_member_data[0]['adviser']
    assert updated_team_members[0].role == new_team_member_data[0]['role']
    assert updated_team_members[1].adviser == new_team_member_data[1]['adviser']
    assert updated_team_members[1].role == new_team_member_data[1]['role']
    assert project.team_members.count() == 2
