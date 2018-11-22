import factory
import pytest
from django.conf import settings

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyCoreTeamMemberFactory,
    CompanyFactory,
    ContactFactory,
)


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestCompany:
    """Tests for the company model."""

    def test_get_absolute_url(self):
        """Test that Company.get_absolute_url() returns the correct URL."""
        company = CompanyFactory.build()
        assert company.get_absolute_url() == (
            f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}/{company.pk}'
        )

    @pytest.mark.parametrize(
        'build_global_headquarters',
        (
            lambda: CompanyFactory.build(),
            lambda: None,
        ),
        ids=('as_subsidiary', 'as_global_headquarters'),
    )
    def test_get_group_global_headquarters(self, build_global_headquarters):
        """
        Test that `get_group_global_headquarters` returns `self` if the company has
        no `global_headquarters` or the `global_headquarters` otherwise.
        """
        company = CompanyFactory.build(
            global_headquarters=build_global_headquarters(),
        )

        expected_group_global_headquarters = company.global_headquarters or company
        assert company.get_group_global_headquarters() == expected_group_global_headquarters

    @pytest.mark.parametrize(
        'build_global_headquarters',
        (
            lambda gam: CompanyFactory(one_list_account_owner=gam),
            lambda gam: None,
        ),
        ids=('as_subsidiary', 'as_global_headquarters'),
    )
    @pytest.mark.parametrize(
        'with_global_account_manager',
        (True, False),
        ids=lambda val: f'{"With" if val else "Without"} global account manager',
    )
    def test_get_one_list_group_core_team(
        self,
        build_global_headquarters,
        with_global_account_manager,
    ):
        """
        Test that `get_one_list_group_core_team` returns the Core Team of `self` if the company
        has no `global_headquarters` or the one of its `global_headquarters` otherwise.
        """
        team_member_advisers = AdviserFactory.create_batch(
            3,
            first_name=factory.Iterator(
                ('Adam', 'Barbara', 'Chris'),
            ),
        )
        global_account_manager = team_member_advisers[0] if with_global_account_manager else None

        global_headquarters = build_global_headquarters(global_account_manager)
        company = CompanyFactory(
            global_headquarters=global_headquarters,
            one_list_account_owner=None if global_headquarters else global_account_manager,
        )
        group_global_headquarters = company.global_headquarters or company
        CompanyCoreTeamMemberFactory.create_batch(
            len(team_member_advisers),
            company=group_global_headquarters,
            adviser=factory.Iterator(team_member_advisers),
        )

        core_team = company.get_one_list_group_core_team()
        assert core_team == [
            {
                'adviser': adviser,
                'is_global_account_manager': adviser is global_account_manager,
            }
            for adviser in team_member_advisers
        ]


class TestContact:
    """Tests for the contact model."""

    def test_get_absolute_url(self):
        """Test that Contact.get_absolute_url() returns the correct URL."""
        contact = ContactFactory.build()
        assert contact.get_absolute_url() == (
            f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["contact"]}/{contact.pk}'
        )
