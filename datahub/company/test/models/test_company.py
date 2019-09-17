import pytest
from django.db.utils import IntegrityError
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

    def test_model_null(self):
        """
        Check if trying to create a new company that has `pending_dnb_investigation`
        set to None raises an error.
        """
        with pytest.raises(IntegrityError):
            CompanyFactory(pending_dnb_investigation=None)

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


@pytest.mark.django_db
class TestDNBInvestigationData:
    """
    Test `dnb_investigation_data`.
    """

    @pytest.mark.parametrize(
        'override',
        (
            {},
            {'dnb_investigation_data': None},
        ),
    )
    def test_null(self, override):
        """
        Test that dnb_investigation_data is nullable.
        """
        company = CompanyFactory(**override)
        db_company = Company.objects.get(id=company.id)
        assert db_company.dnb_investigation_data is None

    @pytest.mark.parametrize(
        'investigation_data',
        (
            {},
            {'foo': 'bar'},
        ),
    )
    def test_value(self, investigation_data):
        """
        Test that dnb_investigation_data can be set.
        """
        company = CompanyFactory(dnb_investigation_data=investigation_data)
        db_company = Company.objects.get(id=company.id)
        assert db_company.dnb_investigation_data == investigation_data

    @pytest.mark.parametrize(
        'investigation_data',
        (
            None,
            {},
            {'foo': 'bar'},
            {'telephone_number': '12345678'},
            {'telephone_number': None},
        ),
    )
    def test_get_dnb_investigation_context(self, investigation_data):
        """
        Test if get_dnb_investigation_context returns a dict with sensible
        values for the required fields.
        """
        company = CompanyFactory(dnb_investigation_data=investigation_data)
        investigation_data = investigation_data or {}
        assert company.get_dnb_investigation_context() == {
            'name': company.name,
            'address': {
                'line_1': company.address_1,
                'line_2': company.address_2,
                'town': company.address_town,
                'county': company.address_county,
                'country': company.address_country.name,
                'postcode': company.address_postcode,
            },
            'website': company.website,
            'telephone_number': investigation_data.get('telephone_number'),
        }
