import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.omis.order.test.factories import OrderWithAcceptedQuoteFactory
from datahub.omis.payment.constants import PaymentMethod
from datahub.omis.payment.utils import trasform_govuk_payment_to_omis_payment_data


class TestGetOmisPaymentDataFromGovukPayment:
    """
    Tests for the `trasform_govuk_payment_to_omis_payment_data` function.
    """

    def test_with_non_success_response_returns_none(self):
        """
        Test that if the status of the GOV.UK payment is not `success`,
        the method returns None
        """
        govuk_payment = {
            'state': {
                'status': 'created',
            },
        }
        assert not trasform_govuk_payment_to_omis_payment_data(govuk_payment)

    def test_data(self):
        """Test the transformed data from a GOV.UK payment."""
        govuk_payment = {
            'amount': 1234,
            'state': {'status': 'success'},
            'email': 'email@example.com',
            'created_date': '2018-02-13T14:56:56.734Z',
            'reference': '12345',
            'card_details': {
                'last_digits_card_number': '1111',
                'cardholder_name': 'John Doe',
                'expiry_date': '01/20',
                'billing_address': {
                    'line1': 'line 1 address',
                    'line2': 'line 2 address',
                    'postcode': 'SW1A 1AA',
                    'city': 'London',
                    'country': 'GB',
                },
                'card_brand': 'Visa',
            },
        }

        payment_data = trasform_govuk_payment_to_omis_payment_data(govuk_payment)

        assert payment_data == {
            'amount': 1234,
            'method': PaymentMethod.CARD,
            'received_on': dateutil_parse('2018-02-13').date(),
            'transaction_reference': '12345',
            'cardholder_name': 'John Doe',
            'card_brand': 'Visa',
            'billing_email': 'email@example.com',
            'billing_address_1': 'line 1 address',
            'billing_address_2': 'line 2 address',
            'billing_address_town': 'London',
            'billing_address_postcode': 'SW1A 1AA',
            'billing_address_country': 'GB',
        }

    @pytest.mark.django_db
    def test_when_card_detail_fields_are_none(self):
        """
        Test if card details with billing and card holder name is set to ""
        """
        order = OrderWithAcceptedQuoteFactory()

        payment_data = trasform_govuk_payment_to_omis_payment_data(
            {
                'card_details': {
                    'billing_address': None,
                    'card_brand': 'Mastercard',
                    'card_type': 'debit',
                    'cardholder_name': None,
                    'expiry_date': '01/29',
                    'first_digits_card_number': None,
                    'last_digits_card_number': '1234',
                    'wallet_type': 'Apple Pay',
                },
                'state': {'status': 'success'},
                'amount': 100000,
                'created_date': '2017-01-02',
                'reference': 'FA1234',
                'email': 'fake@fake.com',
            },
        )
        order.mark_as_paid(
            by=None,
            payments_data=[payment_data],
        )
        assert payment_data == {
            'amount': 100000,
            'method': PaymentMethod.CARD,
            'received_on': dateutil_parse('2017-01-02').date(),
            'transaction_reference': 'FA1234',
            'cardholder_name': '',
            'card_brand': 'Mastercard',
            'billing_email': 'fake@fake.com',
            'billing_address_1': '',
            'billing_address_2': '',
            'billing_address_town': '',
            'billing_address_postcode': '',
            'billing_address_country': '',
        }
