import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.tests.factories import KingsAwardRecipientFactory
from datahub.core.test_utils import APITestMixin, create_test_user


class TestGetCompanyKingsAwards(APITestMixin):
    """Tests the GET endpoint that lists all King's Awards for a specific company."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if no credentials are provided."""
        company = CompanyFactory()
        url = reverse('api-v4:company:kings-awards-list', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        ('permission_codenames', 'expected_status'),
        [
            ((), status.HTTP_403_FORBIDDEN),
            (('view_company',), status.HTTP_200_OK),
        ],
    )
    def test_inherits_permission_from(self, permission_codenames, expected_status):
        """Test that action permission is inherited from company viewing permission."""
        company = CompanyFactory()
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:kings-awards-list', kwargs={'pk': company.id})

        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_returns_404_for_non_existent_company(self):
        """Test that a 404 is returned for a non-existent company ID."""
        non_existent_pk = '00000000-0000-0000-0000-000000000000'
        url = reverse('api-v4:company:kings-awards-list', kwargs={'pk': non_existent_pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_empty_list_for_company_with_no_awards(self):
        """Test that an empty list is returned for a company with no awards."""
        company = CompanyFactory()
        url = reverse('api-v4:company:kings-awards-list', kwargs={'pk': company.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_returns_awards_for_company(self):
        """Test that awards for the specified company are returned and ordered correctly."""
        company = CompanyFactory()
        other_company = CompanyFactory()

        award1 = KingsAwardRecipientFactory(company=company, year_awarded=2023)
        award2 = KingsAwardRecipientFactory(company=company, year_awarded=2025)
        award3 = KingsAwardRecipientFactory(company=company, year_awarded=2024)
        KingsAwardRecipientFactory(
            company=other_company, year_awarded=2024,
        )  # award for another company

        url = reverse('api-v4:company:kings-awards-list', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) == 3

        # assert descending by year_awarded
        expected_ids_in_order = [str(award2.id), str(award3.id), str(award1.id)]
        actual_ids_in_order = [result['id'] for result in response_data]
        assert actual_ids_in_order == expected_ids_in_order

        # assert structure
        first_result = response_data[0]
        assert first_result['id'] == str(award2.id)
        assert first_result['company']['id'] == str(company.id)
        assert first_result['company']['name'] == company.name
        assert first_result['year_awarded'] == award2.year_awarded
        assert first_result['category'] == award2.get_category_display()
        assert first_result['citation'] == award2.citation
        assert first_result['year_expired'] == award2.year_expired
