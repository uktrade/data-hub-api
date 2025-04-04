import pytest

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
)
from datahub.core import constants
from datahub.investment.project.serializers import (
    IProjectSerializer,
    IProjectTeamMemberListSerializer,
    IProjectTeamMemberSerializer,
)
from datahub.investment.project.test.factories import (
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
)

pytestmark = pytest.mark.django_db


class TestIProjectTeamMemberListSerializer:
    """Tests for IProjectTeamMemberListSerializer."""

    def test_team_member_list_update_remove_all(self):
        """Tests removing all team members."""
        project = InvestmentProjectFactory()

        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2,
            investment_project=project,
        )

        child_serializer = IProjectTeamMemberSerializer()
        serializer = IProjectTeamMemberListSerializer(child=child_serializer)

        assert serializer.update(team_members, []) == []
        assert project.team_members.count() == 0

    def test_team_member_list_update_mixed_changes(self):
        """Tests making mixed changes to team members."""
        project = InvestmentProjectFactory()

        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2,
            investment_project=project,
            role='old role',
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

    def test_team_member_list_update_change_only(self):
        """Tests updating existing team members."""
        project = InvestmentProjectFactory()

        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2,
            investment_project=project,
            role='old role',
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

    def test_team_member_list_update_add_only(self):
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


class TestIProjectSerializer:
    """Tests for IProjectSerializer."""

    def test_estimated_land_date_is_required_for_new_project(self):
        """Tests estimated land date is required for new projects."""
        project_data = {'estimated_land_date': None}
        serializer = IProjectSerializer(data=project_data)
        assert not serializer.is_valid()
        assert serializer.errors['estimated_land_date'] == ['This field is required.']

    def test_estimated_land_date_cannot_be_erased_if_not_allowed_to_be_blank(self):
        """Tests updating estimated land date cannot be set to a blank if not allowed."""
        project = InvestmentProjectFactory()
        project_data = {'estimated_land_date': None}
        serializer = IProjectSerializer(project, data=project_data, partial=True)
        assert not serializer.is_valid()
        assert serializer.errors['estimated_land_date'] == ['This field is required.']

    def test_estimated_land_date_can_be_erased_if_allowed_to_be_blank(self):
        """Tests updating estimated land date to a blank when allowed."""
        project = InvestmentProjectFactory(allow_blank_estimated_land_date=True)
        project_data = {'estimated_land_date': None}
        serializer = IProjectSerializer(project, data=project_data, partial=True)
        assert serializer.is_valid()

    def test_country_investment_originates_from(self):
        """Tests updating the country the investment originates from on an investment project."""
        project = InvestmentProjectFactory(investor_company=None)
        project_data = {
            'country_investment_originates_from': {'id': constants.Country.argentina.value.id},
        }
        serializer = IProjectSerializer(project, data=project_data, partial=True)
        assert serializer.is_valid()
        assert (
            str(
                serializer.validated_data['country_investment_originates_from'],
            )
            == constants.Country.argentina.value.name
        )

    def test_uk_company_address_fields(self):
        """Tests address fields are sent with UK company nested object."""
        project = InvestmentProjectFactory(uk_company=CompanyFactory())
        serializer = IProjectSerializer(project)
        assert serializer.data['uk_company']['id'] == str(project.uk_company.id)
        assert serializer.data['uk_company']['name'] == project.uk_company.name
        assert serializer.data['uk_company']['address_1'] == project.uk_company.address_1
        assert serializer.data['uk_company']['address_2'] == project.uk_company.address_2
        assert serializer.data['uk_company']['address_town'] == project.uk_company.address_town
        assert (
            serializer.data['uk_company']['address_postcode']
            == project.uk_company.address_postcode
        )
