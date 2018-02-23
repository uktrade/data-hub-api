import factory
import pytest

from datahub.company.test.factories import (
    CompaniesHouseCompanyFactory, CompanyFactory, ContactFactory
)
from datahub.core import constants
from .factories import OrderFactory
from ..utils import populate_billing_data

pytestmark = pytest.mark.django_db


class CompanyWithRegAddressFactory(CompanyFactory):
    """Factory for a company with all registered address filled in."""

    registered_address_1 = factory.Faker('text')
    registered_address_2 = factory.Faker('text')
    registered_address_town = factory.Faker('text')
    registered_address_county = factory.Faker('text')
    registered_address_postcode = factory.Faker('text')
    registered_address_country_id = constants.Country.japan.value.id
    company_number = factory.LazyFunction(
        lambda: CompaniesHouseCompanyFactory().company_number
    )


class OrderWithoutBillingDataFactory(OrderFactory):
    """Factory for order without billing fields."""

    billing_company_name = ''
    billing_contact_name = ''
    billing_email = ''
    billing_phone = ''
    billing_address_1 = ''
    billing_address_2 = ''
    billing_address_town = ''
    billing_address_county = ''
    billing_address_postcode = ''
    billing_address_country = None


class TestPopulateBillingData:
    """Tests for the populate_billing_data logic."""

    def test_with_empty_order(self):
        """
        Test that an order without any of the billing fields filled in is populated
        with the company/contact details.
        """
        contact = ContactFactory()
        company = CompanyWithRegAddressFactory()
        order = OrderWithoutBillingDataFactory(
            company=company,
            contact=contact
        )

        populate_billing_data(order)

        assert not order.billing_contact_name
        assert not order.billing_email
        assert not order.billing_phone

        assert order.billing_company_name == company.name
        assert order.billing_address_1 == company.registered_address_1
        assert order.billing_address_2 == company.registered_address_2
        assert order.billing_address_town == company.registered_address_town
        assert order.billing_address_county == company.registered_address_county
        assert order.billing_address_postcode == company.registered_address_postcode
        assert order.billing_address_country == company.registered_address_country

    def test_with_null_values(self):
        """
        Test that if a company has address fields with null values, they are translated into
        empty strings when copied over.

        This is because the Company model contains a bug that allows null values for CharFields.
        """
        company = CompanyFactory(
            registered_address_2=None,
            registered_address_county=None,
            registered_address_postcode=None,
            registered_address_country_id=None
        )
        order = OrderFactory(
            company=company,
            billing_address_2='',
            billing_address_county='',
            billing_address_postcode='',
            billing_address_country=None
        )

        populate_billing_data(order)

        assert order.billing_address_2 == ''
        assert order.billing_address_county == ''
        assert order.billing_address_postcode == ''
        assert order.billing_address_country is None

    def test_with_already_populated_billing_detail(self):
        """
        Test that if the order has an order details field already populated,
        it does not get overridden.
        """
        billing_company_name = 'My Corp'

        contact = ContactFactory()
        order = OrderFactory(
            contact=contact,
            billing_company_name=billing_company_name,
        )

        populate_billing_data(order)

        assert order.billing_company_name == billing_company_name

    @pytest.mark.parametrize(
        'billing_address',
        (
            {
                'billing_address_1': 'Populated address 1',
                'billing_address_2': 'Populated address 2',
                'billing_address_town': 'Populated address town',
                'billing_address_county': 'Populated address county',
                'billing_address_postcode': 'Populated address postcode',
                'billing_address_country_id': constants.Country.italy.value.id
            },
            {
                'billing_address_1': '',
                'billing_address_2': '',
                'billing_address_town': 'Populated address town',
                'billing_address_county': '',
                'billing_address_postcode': '',
                'billing_address_country_id': constants.Country.italy.value.id
            },
        )
    )
    def test_with_already_populated_billing_address(self, billing_address):
        """
        Test that if the order has some billing address fields already populated,
        none of the address fields get overridden.
        """
        company = CompanyWithRegAddressFactory()
        order = OrderFactory(
            company=company,
            **billing_address
        )

        populate_billing_data(order)

        # check that the fields didn't get overridden
        for field in billing_address:
            assert str(getattr(order, field)) == str(billing_address[field])
