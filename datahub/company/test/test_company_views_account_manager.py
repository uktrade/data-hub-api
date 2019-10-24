import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.constants import OneListTierID
from datahub.company.models import CompanyPermission, OneListTier
from datahub.company.test.factories import AdviserFactory, CompanyFactory, SubsidiaryFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    random_obj_for_model,
    random_obj_for_queryset,
)


@pytest.fixture
def international_trade_adviser():
    """An adviser with permission to change regional account managers."""
    permission_codenames = [
        CompanyPermission.change_company,
        CompanyPermission.change_regional_account_manager,
    ]

    return create_test_user(permission_codenames=permission_codenames, dit_team=None)


def _random_non_ita_one_list_tier():
    queryset = OneListTier.objects.exclude(
        pk=OneListTierID.tier_d_international_trade_advisers.value,
    )
    return random_obj_for_queryset(queryset)


class TestSelfAssignCompanyAccountManagerView(APITestMixin):
    """
    Tests for the self-assign company account manager view.

    (Implemented in CompanyViewSet.self_assign_account_manager().)
    """

    @staticmethod
    def _get_url(company):
        return reverse('api-v4:company:self-assign-account-manager', kwargs={'pk': company.pk})

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if no credentials are provided."""
        company = CompanyFactory()
        url = self._get_url(company)
        response = api_client.post(url)
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

        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'company_factory',
        (
            pytest.param(
                lambda: CompanyFactory(one_list_account_owner=None, one_list_tier=None),
                id='no-existing-account-manager',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_account_owner=AdviserFactory(),
                    one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
                ),
                id='existing-international-trade-adviser-account-manager',
            ),
        ),
    )
    @pytest.mark.django_db
    def test_assigns_account_manager(self, company_factory, international_trade_adviser):
        """
        Test that an account manager can be assigned to:

        - a company not on the One List
        - a company on the One List tier 'Tier D - International Trade Adviser Accounts'
        """
        company = company_factory()
        api_client = self.create_api_client(user=international_trade_adviser)
        url = self._get_url(company)

        response = api_client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        assert company.one_list_account_owner == international_trade_adviser
        assert company.one_list_tier_id == OneListTierID.tier_d_international_trade_advisers.value

    @pytest.mark.parametrize(
        'company_factory,expected_errors',
        (
            pytest.param(
                lambda: SubsidiaryFactory(
                    global_headquarters__one_list_tier=random_obj_for_model(OneListTier),
                    global_headquarters__one_list_account_owner=AdviserFactory(),
                ),
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        "A lead adviser can't be set on a subsidiary of a One List company.",
                    ],
                },
                id='subsidiary-of-one-list-company',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_tier=_random_non_ita_one_list_tier(),
                    one_list_account_owner=AdviserFactory(),
                ),
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        "A lead adviser can't be set for companies on this One List tier.",
                    ],
                },
                id='already-on-another-one-list-tier',
            ),
        ),
    )
    @pytest.mark.django_db
    def test_validation(self, company_factory, expected_errors, international_trade_adviser):
        """
        Test that an account manager can't be assigned to:

        - a company on a One List tier other than 'Tier D - International Trade Adviser Accounts'
        - a company on that is a subsidiary of any One List company
        """
        company = company_factory()
        api_client = self.create_api_client(user=international_trade_adviser)
        url = self._get_url(company)

        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors
