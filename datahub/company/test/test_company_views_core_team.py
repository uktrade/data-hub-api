import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core.test_utils import APITestMixin


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
