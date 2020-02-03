import uuid
from operator import attrgetter

import pytest

from datahub.company.test.factories import (
    CompanyFactory,
    ContactFactory,
)
from datahub.core import constants
from datahub.core.constants import Country
from datahub.omis.order.test.factories import OrderFactory
from datahub.omis.order.utils import compose_official_address, populate_billing_data

pytestmark = pytest.mark.django_db


class TestPopulateBillingData:
    """Tests for the populate_billing_data logic."""

    @pytest.mark.parametrize(
        'initial_model_values,expected_billing_address_fields',
        (
            # registered address
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,
                },
                {
                    'billing_address_1': '2',
                    'billing_address_2': 'Main Road',
                    'billing_address_town': 'London',
                    'billing_address_county': 'Greenwich',
                    'billing_address_postcode': 'SE10 9NN',
                    'billing_address_country_id': uuid.UUID(Country.united_kingdom.value.id),
                },
            ),

            # registered address blank
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '',
                    'registered_address_2': '',
                    'registered_address_town': '',
                    'registered_address_county': None,
                    'registered_address_postcode': '',
                    'registered_address_country_id': None,
                },
                {
                    'billing_address_1': '1',
                    'billing_address_2': 'Hello st.',
                    'billing_address_town': 'Muckamore',
                    'billing_address_county': 'Antrim',
                    'billing_address_postcode': 'BT41 4QE',
                    'billing_address_country_id': uuid.UUID(Country.ireland.value.id),
                },
            ),

            # very minimal address
            (
                {
                    'address_1': '1',
                    'address_2': '',
                    'address_town': '',
                    'address_county': None,
                    'address_postcode': '',
                    'address_country_id': None,

                    'registered_address_1': None,
                    'registered_address_2': None,
                    'registered_address_town': None,
                    'registered_address_county': None,
                    'registered_address_postcode': None,
                    'registered_address_country_id': None,
                },
                {
                    'billing_address_1': '1',
                    'billing_address_2': '',
                    'billing_address_town': '',
                    'billing_address_county': '',
                    'billing_address_postcode': '',
                    'billing_address_country': None,
                },
            ),
        ),
    )
    def test_with_empty_order(self, initial_model_values, expected_billing_address_fields):
        """
        Test that an order without any of the billing fields filled in is populated
        with the company/contact details.
        """
        company = CompanyFactory.build(**initial_model_values)
        order = OrderFactory.build(
            billing_company_name='',
            billing_contact_name='',
            billing_email='',
            billing_phone='',
            billing_address_1='',
            billing_address_2='',
            billing_address_town='',
            billing_address_county='',
            billing_address_postcode='',
            billing_address_country_id=None,

            company=company,
            contact=ContactFactory.build(),
        )

        populate_billing_data(order)

        assert not order.billing_contact_name
        assert not order.billing_email
        assert not order.billing_phone
        assert order.billing_company_name == company.name

        actual_billing_address = {
            field_name: getattr(order, field_name)
            for field_name in expected_billing_address_fields
        }
        assert actual_billing_address == expected_billing_address_fields

    def test_with_already_populated_billing_company_name(self):
        """
        Test that if the billing company name for an order is already set,
        it does not get overridden.
        """
        billing_company_name = 'My Corp'

        order = OrderFactory.build(
            contact=ContactFactory.build(),
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
                'billing_address_country_id': uuid.UUID(constants.Country.italy.value.id),
            },
            {
                'billing_address_1': '',
                'billing_address_2': '',
                'billing_address_town': 'Populated address town',
                'billing_address_county': '',
                'billing_address_postcode': '',
                'billing_address_country_id': uuid.UUID(constants.Country.italy.value.id),
            },
        ),
    )
    def test_with_already_populated_billing_address(self, billing_address):
        """
        Test that if the order has some billing address fields already populated,
        none of the address fields get overridden.
        """
        company = CompanyFactory.build(
            address_1='1',
            address_2='Hello st.',
            address_town='Muckamore',
            address_county='Antrim',
            address_postcode='BT41 4QE',
            address_country_id=Country.ireland.value.id,
        )
        order = OrderFactory.build(
            company=company,
            **billing_address,
        )

        populate_billing_data(order)

        # check that the fields didn't get overridden
        actual_billing_address = {
            field_name: getattr(order, field_name)
            for field_name in billing_address
        }
        assert actual_billing_address == billing_address


class TestComposeOfficialAddress:
    """Tests for the compose_official_address function."""

    @pytest.mark.parametrize(
        'initial_model_values,expected_address_values',
        (
            # registered address
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,
                },
                {
                    'line_1': '2',
                    'line_2': 'Main Road',
                    'town': 'London',
                    'county': 'Greenwich',
                    'postcode': 'SE10 9NN',
                    'country.pk': uuid.UUID(Country.united_kingdom.value.id),
                },
            ),

            # registered address blank
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '',
                    'registered_address_2': '',
                    'registered_address_town': '',
                    'registered_address_county': None,
                    'registered_address_postcode': '',
                    'registered_address_country_id': None,
                },
                {
                    'line_1': '1',
                    'line_2': 'Hello st.',
                    'town': 'Muckamore',
                    'county': 'Antrim',
                    'postcode': 'BT41 4QE',
                    'country.pk': uuid.UUID(Country.ireland.value.id),
                },
            ),

            # very minimal address
            (
                {
                    'address_1': '1',
                    'address_2': '',
                    'address_town': '',
                    'address_county': None,
                    'address_postcode': '',
                    'address_country_id': None,

                    'registered_address_1': '',
                    'registered_address_2': '',
                    'registered_address_town': '',
                    'registered_address_county': None,
                    'registered_address_postcode': '',
                    'registered_address_country_id': None,
                },
                {
                    'line_1': '1',
                    'line_2': '',
                    'town': '',
                    'county': None,
                    'postcode': '',
                    'country': None,
                },
            ),
        ),
    )
    def test(self, initial_model_values, expected_address_values):
        """
        Test that registered address is used if defined or address otherwise.
        """
        company = CompanyFactory.build(**initial_model_values)
        address = compose_official_address(company)

        actual_address = {
            attr_name: attrgetter(attr_name)(address)
            for attr_name in expected_address_values
        }
        assert actual_address == expected_address_values
