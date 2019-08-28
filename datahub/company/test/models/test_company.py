import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.constants import (
    Country,
    Sector,
    UKRegion,
)
from datahub.core.test_utils import APITestMixin


@pytest.mark.django_db
class TestPendingDNBInvestigation(APITestMixin):
    """
    Test if the `pending_dnb_investigation` field is set to False
    when a comapny is created in DataHub.
    """

    def test_model(self):
        """
        Check if a newly created company has `pending_dnb_investigation`
        set to False.
        """
        company = CompanyFactory()
        assert not Company.objects.get(
            id=company.id,
        ).pending_dnb_investigation

    @pytest.mark.parametrize(
        'company_data',
        (
            {
                'name': 'Acme',
                'business_type': {
                    'id': BusinessTypeConstant.company.value.id,
                },
                'address': {
                    'line_1': '75 Stramford Road',
                    'town': 'London',
                    'country': {
                        'id': Country.united_kingdom.value.id,
                    },
                },
                'sector': Sector.renewable_energy_wind.value.id,
                'uk_region': {
                    'id': UKRegion.england.value.id,
                },
            },
        ),
    )
    @pytest.mark.django_db
    def test_company_post(self, company_data):
        """
        Test if a company created via create-company endpoint has
        `pending_dnb_investigation` set to False.
        """
        url = reverse('api-v4:company:collection')
        response = self.api_client.post(
            url,
            company_data,
        )
        assert response.status_code == status.HTTP_201_CREATED

        company = Company.objects.get(
            id=response.json()['id'],
        )
        assert not company.pending_dnb_investigation
