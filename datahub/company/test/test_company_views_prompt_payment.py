import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.company_activity.tests.factories import PromptPaymentsFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime

pytestmark = pytest.mark.django_db


class TestGetCompanyPromptPayments(APITestMixin):
    """Tests the GET endpoint that lists all PromptPayments records for a specific company."""

    def _get_url(self, company_pk):
        return reverse('api-v4:company:prompt-payments-list', kwargs={'pk': company_pk})

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if no credentials are provided."""
        company = CompanyFactory()
        url = self._get_url(company.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        ('permission_codenames', 'expected_status'),
        [
            ((), status.HTTP_403_FORBIDDEN),
            ((CompanyPermission.view_company,), status.HTTP_200_OK),
        ],
    )
    def test_permission_checking(self, permission_codenames, expected_status):
        """Test that action permission is checked."""
        company = CompanyFactory()
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        url = self._get_url(company.pk)

        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_returns_404_for_non_existent_company(self):
        """Test that a 404 is returned for a non-existent company ID."""
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
        )
        api_client = self.create_api_client(user=user)
        non_existent_pk = '00000000-0000-0000-0000-000000000000'
        url = self._get_url(non_existent_pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_returns_empty_list_for_company_with_no_prompt_payments(self):
        """Test that an empty list is returned for a company with no prompt payments."""
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = self._get_url(company.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_returns_prompt_payments_for_company(self):
        """Test that prompt payments for the specified company are returned and ordered correctly."""
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        other_company = CompanyFactory()

        pp1 = PromptPaymentsFactory(
            company=company,
            filing_date='2025-01-15',
            reporting_period_end_date='2024-12-31',
        )
        pp2 = PromptPaymentsFactory(
            company=company,
            filing_date='2025-03-10',
            reporting_period_end_date='2025-02-28',
        )
        pp3 = PromptPaymentsFactory(
            company=company,
            filing_date='2025-03-10',
            reporting_period_end_date='2025-01-31',
        )
        PromptPaymentsFactory(company=other_company)

        url = self._get_url(company.pk)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) == 3

        expected_ids_in_order = [str(pp2.id), str(pp3.id), str(pp1.id)]
        actual_ids_in_order = [result['id'] for result in response_data]
        assert actual_ids_in_order == expected_ids_in_order

        first_result = response_data[0]
        assert first_result['id'] == str(pp2.id)
        assert first_result['company']['id'] == str(company.id)
        assert first_result['company']['name'] == company.name
        assert first_result['reporting_period_start_date'] == str(pp2.reporting_period_start_date)
        assert first_result['average_paid_days'] == pp2.average_paid_days
        assert first_result['created_on'] == format_date_or_datetime(pp2.created_on)
