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
def one_list_editor():
    """An adviser with permission to change one list company."""
    permission_codenames = [
        CompanyPermission.change_company,
        CompanyPermission.change_one_list_tier_and_global_account_manager,
    ]

    return create_test_user(permission_codenames=permission_codenames, dit_team=None)


def _random_non_ita_one_list_tier():
    queryset = OneListTier.objects.exclude(
        pk=OneListTierID.tier_d_international_trade_advisers.value,
    )
    return random_obj_for_queryset(queryset)


class TestUpdateOneListTierAndGlobalAccountManager(APITestMixin):
    """
    Tests for the update company One List tier and global account manager view.

    (Implemented in CompanyViewSet.update_one_list_tier_and_global_account_manager().)
    """

    @staticmethod
    def _get_url(company):
        return reverse(
            'api-v4:company:assign-one-list-tier-and-global-account-manager',
            kwargs={'pk': company.pk},
        )

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
            (CompanyPermission.change_one_list_tier_and_global_account_manager,),
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
                id='no-existing-global-account-manager',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_account_owner=AdviserFactory(),
                    one_list_tier=_random_non_ita_one_list_tier(),
                ),
                id='existing-global-account-manager',
            ),
        ),
    )
    @pytest.mark.django_db
    def test_assigns_one_list_tier_and_global_account_manager(
        self,
        company_factory,
        one_list_editor,
    ):
        """
        Test that a One List tier and global account manager can be assigned to:

        - a company not on the One List
        - a company on random One List tier except 'Tier D - International Trade Adviser Accounts'
        """
        company = company_factory()
        api_client = self.create_api_client(user=one_list_editor)
        url = self._get_url(company)

        new_one_list_tier = _random_non_ita_one_list_tier()

        global_account_manager = AdviserFactory()

        response = api_client.post(
            url,
            {
                'one_list_tier': new_one_list_tier.id,
                'global_account_manager': global_account_manager.id,
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        assert company.one_list_account_owner == global_account_manager
        assert company.one_list_tier_id == new_one_list_tier.pk
        assert company.modified_by == one_list_editor

    @pytest.mark.parametrize(
        'company_factory,adviser_id_fn,new_one_list_tier_id_fn,expected_errors',
        (
            pytest.param(
                lambda: CompanyFactory(
                    one_list_tier=random_obj_for_model(OneListTier),
                    one_list_account_owner=AdviserFactory(),
                ),
                lambda: None,
                lambda: None,
                {
                    'global_account_manager': [
                        'This field may not be null.',
                    ],
                    'one_list_tier': [
                        'This field may not be null.',
                    ],
                },
                id='required',
            ),
            pytest.param(
                lambda: SubsidiaryFactory(
                    global_headquarters__one_list_tier=random_obj_for_model(OneListTier),
                    global_headquarters__one_list_account_owner=AdviserFactory(),
                ),
                lambda: AdviserFactory().pk,
                lambda: _random_non_ita_one_list_tier().pk,
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        'A subsidiary cannot be on One List.',
                    ],
                },
                id='subsidiary-of-one-list-company',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
                    one_list_account_owner=AdviserFactory(),
                ),
                lambda: AdviserFactory().pk,
                lambda: _random_non_ita_one_list_tier().pk,
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        'A company on this One List tier can only be changed by ITA.',
                    ],
                },
                id='company-one-list-details-can-only-be-changed-by-ita',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_tier=_random_non_ita_one_list_tier(),
                    one_list_account_owner=AdviserFactory(),
                ),
                lambda: AdviserFactory().pk,
                lambda: OneListTierID.tier_d_international_trade_advisers.value,
                {
                    'one_list_tier': [
                        'A company can only have this One List tier assigned by ITA.',
                    ],
                },
                id='company-can-only-have-this-one-list-tier-assigned-by-ita',
            ),
        ),
    )
    @pytest.mark.django_db
    def test_validation(
        self,
        company_factory,
        adviser_id_fn,
        new_one_list_tier_id_fn,
        expected_errors,
        one_list_editor,
    ):
        """
        Test that a One List tier and account manager can't be assigned to:

        - a company on a One List tier 'Tier D - International Trade Adviser Accounts'
        - a company on that is a subsidiary of any One List company
        """
        company = company_factory()
        api_client = self.create_api_client(user=one_list_editor)
        url = self._get_url(company)

        response = api_client.post(
            url,
            {
                'one_list_tier': new_one_list_tier_id_fn(),
                'global_account_manager': adviser_id_fn(),
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors


class TestRemoveCompanyFromOneList(APITestMixin):
    """
    Tests for the remove company from One List view.

    (Implemented in CompanyViewSet.remove_from_one_list().)
    """

    @staticmethod
    def _get_url(company):
        return reverse('api-v4:company:remove-from-one-list', kwargs={'pk': company.pk})

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
                id='not-on-one-list',
            ),
            pytest.param(
                lambda: CompanyFactory(
                    one_list_account_owner=AdviserFactory(),
                    one_list_tier_id=_random_non_ita_one_list_tier().pk,
                ),
                id='existing-one-list-assignment',
            ),
        ),
    )
    @pytest.mark.django_db
    def test_removes_tier_and_global_account_manager(
        self,
        company_factory,
        one_list_editor,
    ):
        """
        Test that a company can be removed from One List:

        - a company not on the One List
        - a company on the One List tier other than 'Tier D - International Trade Adviser Accounts'
        """
        company = company_factory()
        api_client = self.create_api_client(user=one_list_editor)
        url = self._get_url(company)

        response = api_client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        company.refresh_from_db()
        assert company.one_list_account_owner is None
        assert company.one_list_tier is None
        assert company.modified_by == one_list_editor

    @pytest.mark.django_db
    def test_cannot_remove_company_from_tier_d_ita(self, one_list_editor):
        """
        Test that a company can't be removed from One List when on a
        'Tier D - International Trade Adviser Accounts' tier.
        """
        company = CompanyFactory(
            one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value,
            one_list_account_owner=AdviserFactory(),
        )
        api_client = self.create_api_client(user=one_list_editor)
        url = self._get_url(company)

        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            api_settings.NON_FIELD_ERRORS_KEY: [
                'It`s not possible to remove a lead ITA from a company using'
                'One List admin functionality',
            ],
        }
