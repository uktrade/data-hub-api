from dateutil.parser import parse as dateutil_parse

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
