import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyPermission
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.company.test.factories import (
    OneListCoreTeamMemberFactory,
)
from datahub.company.test.utils import random_non_ita_one_list_tier
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)


@pytest.fixture
def one_list_company():
    """Get One List company."""
    yield CompanyFactory(
        global_headquarters=None,
        one_list_tier=random_non_ita_one_list_tier(),
        one_list_account_owner=AdviserFactory(),
    )


class TestOneListGroupCoreTeam(APITestMixin):
    """Tests for getting the One List Core Team of a company's group."""

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=None),
            ),
            # as single company
            lambda: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=None,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    def test_empty_list(self, build_company):
        """
        Test that if there's no Global Account Manager and no Core Team
        member for a company's Global Headquarters, the endpoint returns
        an empty list.
        """
        company = build_company()

        url = reverse(
            'api-v4:company:one-list-group-core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda gam: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=gam),
            ),
            # as single company
            lambda gam: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=gam,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    def test_with_only_global_account_manager(self, build_company):
        """
        Test that if there is a Global Account Manager but no Core Team
        member for a company's Global Headquarters, the endpoint returns
        a list with only that adviser in it.
        """
        global_account_manager = AdviserFactory()
        company = build_company(global_account_manager)

        url = reverse(
            'api-v4:company:one-list-group-core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(global_account_manager.pk),
                    'name': global_account_manager.name,
                    'first_name': global_account_manager.first_name,
                    'last_name': global_account_manager.last_name,
                    'contact_email': global_account_manager.contact_email,
                    'dit_team': {
                        'id': str(global_account_manager.dit_team.pk),
                        'name': global_account_manager.dit_team.name,
                        'uk_region': {
                            'id': str(global_account_manager.dit_team.uk_region.pk),
                            'name': global_account_manager.dit_team.uk_region.name,
                        },
                        'country': {
                            'id': str(global_account_manager.dit_team.country.pk),
                            'name': global_account_manager.dit_team.country.name,
                        },
                    },
                },
                'is_global_account_manager': True,
            },
        ]

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda gam: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=gam),
            ),
            # as single company
            lambda gam: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=gam,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    @pytest.mark.parametrize(
        'with_global_account_manager',
        (True, False),
        ids=lambda val: f'{"With" if val else "Without"} global account manager',
    )
    def test_with_core_team_members(self, build_company, with_global_account_manager):
        """
        Test that if there are Core Team members for a company's Global Headquarters,
        the endpoint returns a list with these advisers in it.
        """
        team_member_advisers = AdviserFactory.create_batch(
            3,
            first_name=factory.Iterator(
                ('Adam', 'Barbara', 'Chris'),
            ),
        )
        global_account_manager = team_member_advisers[0] if with_global_account_manager else None

        company = build_company(global_account_manager)
        group_global_headquarters = company.global_headquarters or company
        OneListCoreTeamMemberFactory.create_batch(
            len(team_member_advisers),
            company=group_global_headquarters,
            adviser=factory.Iterator(team_member_advisers),
        )

        url = reverse(
            'api-v4:company:one-list-group-core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(adviser.pk),
                    'name': adviser.name,
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'contact_email': adviser.contact_email,
                    'dit_team': {
                        'id': str(adviser.dit_team.pk),
                        'name': adviser.dit_team.name,
                        'uk_region': {
                            'id': str(adviser.dit_team.uk_region.pk),
                            'name': adviser.dit_team.uk_region.name,
                        },
                        'country': {
                            'id': str(adviser.dit_team.country.pk),
                            'name': adviser.dit_team.country.name,
                        },
                    },
                },
                'is_global_account_manager': adviser is global_account_manager,
            }
            for adviser in team_member_advisers
        ]

    def test_404_with_invalid_company(self):
        """
        Test that if the company doesn't exist, the endpoint returns 404.
        """
        url = reverse(
            'api-v4:company:one-list-group-core-team',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateOneListCoreTeam(APITestMixin):
    """
    Tests for updating the Core Team of One List company.

    (Implemented in CompanyViewSet.remove_from_one_list().)
    """

    @staticmethod
    def _get_url(company):
        return reverse(
            'api-v4:company:update-one-list-core-team',
            kwargs={
                'pk': company.pk,
            },
        )

    def _assert_update_core_team_members(
        self,
        one_list_company,
        existing_team_count,
        new_team_count,
        api_client,
    ):
        url = self._get_url(one_list_company)

        if existing_team_count:
            team_member_advisers = AdviserFactory.create_batch(existing_team_count)
            OneListCoreTeamMemberFactory.create_batch(
                len(team_member_advisers),
                company=one_list_company,
                adviser=factory.Iterator(team_member_advisers),
            )

        old_core_team_members = [
            core_team_member.adviser.id
            for core_team_member in one_list_company.one_list_core_team_members.all()
        ]

        new_core_team_members = [
            adviser.id for adviser in AdviserFactory.create_batch(2)
        ] if new_team_count else []

        response = api_client.patch(
            url,
            {
                'core_team_members':
                [
                    {
                        'adviser': adviser_id,
                    } for adviser_id in new_core_team_members
                ],
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        core_team_members = [
            core_team_member.adviser.id
            for core_team_member in one_list_company.one_list_core_team_members.all()
        ]

        assert core_team_members != old_core_team_members
        assert core_team_members == new_core_team_members

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if no credentials are provided."""
        company = CompanyFactory()
        url = self._get_url(company)
        response = api_client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames',
        (
            (),
            (CompanyPermission.change_company,),
            (CompanyPermission.change_regional_account_manager,),
        ),
    )
    def test_returns_403_if_without_permission(self, permission_codenames):
        """
        Test that a 403 is returned if the user does not have all of the required
        permissions.
        """
        company = CompanyFactory()
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        url = self._get_url(company)

        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'existing_team_count,new_team_count',
        (
            (0, 2),
            (2, 2),
            (2, 0),
        ),
    )
    def test_can_update_core_team_members(
        self,
        one_list_company,
        one_list_editor,
        existing_team_count,
        new_team_count,
    ):
        """Test that core team members can be updated."""
        api_client = self.create_api_client(user=one_list_editor)

        self._assert_update_core_team_members(
            one_list_company, existing_team_count, new_team_count, api_client)

    @pytest.mark.parametrize(
        'existing_team_count,new_team_count',
        (
            (0, 2),
            (2, 2),
            (2, 0),
        ),
    )
    def test_account_manage_can_update_core_team_members(
        self,
        existing_team_count,
        new_team_count,
    ):
        """
        Test that an account manager can update core team members.
        """
        adviser_user = create_test_user(
            permission_codenames=(CompanyPermission.change_company,),
        )
        company = CompanyFactory(
            one_list_account_owner=adviser_user,
            one_list_tier=random_non_ita_one_list_tier(),
        )
        api_client = self.create_api_client(user=adviser_user)

        self._assert_update_core_team_members(
            company, existing_team_count, new_team_count, api_client)

    def test_returns_403_if_account_manager_updates_other_company(self):
        """
        Test that a 403 is returned if an account manager tries to update the core team from
        a company they are not the account manage for.
        """
        account_managers_company = CompanyFactory(
            one_list_account_owner=AdviserFactory(),
            one_list_tier=random_non_ita_one_list_tier(),
        )
        api_client = self.create_api_client(user=account_managers_company.one_list_account_owner)

        company = CompanyFactory()
        url = self._get_url(company)

        response = api_client.patch(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_update_duplicate_core_team_members(self, one_list_company, one_list_editor):
        """Test that duplicate team members cannot be updated."""
        api_client = self.create_api_client(user=one_list_editor)
        url = self._get_url(one_list_company)

        adviser_id = str(AdviserFactory().id)
        response = api_client.patch(
            url,
            {
                'core_team_members':
                [
                    {
                        'adviser': adviser_id,
                    },
                ] * 2,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'core_team_members':
            [
                {
                    'adviser':
                    [
                        'You cannot add the same adviser more than once.',
                    ],
                },
                {
                    'adviser': [
                        'You cannot add the same adviser more than once.',
                    ],
                },
            ],
        }
