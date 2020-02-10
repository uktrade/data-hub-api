from dateutil.parser import parse as dateutil_parse

from datahub.omis.payment.constants import PaymentMethod


def trasform_govuk_payment_to_omis_payment_data(govuk_payment):
    """
    :returns: dict with `payment.Payment` data from a GOV.UK payment data

    :param govuk_payment: GOV.UK payment data
    """
    # if status != success, it's not a successful GOV.UK payment so we can't build
    # the OMIS payment data from it
    if govuk_payment['state']['status'] != 'success':
        return None

    card_details = govuk_payment['card_details']
    billing_address = card_details['billing_address']

    return {
        'amount': govuk_payment['amount'],
        'method': PaymentMethod.CARD,
        'transaction_reference': govuk_payment['reference'],

        # unfortunately GOV.UK Pay doesn't tell us when the payment actually happened
        'received_on': dateutil_parse(govuk_payment['created_date']).date(),

        # card details
        'cardholder_name': card_details['cardholder_name'],
        'card_brand': card_details['card_brand'],
        'billing_email': govuk_payment['email'],
        'billing_address_1': billing_address['line1'],
        'billing_address_2': billing_address['line2'],
        'billing_address_town': billing_address['city'],
        'billing_address_postcode': billing_address['postcode'],
        'billing_address_country': billing_address['country'],
    }
