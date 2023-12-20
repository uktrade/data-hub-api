from datetime import datetime, timedelta

from django.conf import settings

from datahub.export_win.models import CustomerResponseToken


def get_all_fields_for_client_email_receipt(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    details = {
        'customer_email': win_token.email,
        'country_destination': win.country,
        'client_firstname': win_token.first_name,
        'lead_officer_name': win.lead_officer.name,
        'goods_services': win.goods_vs_services,
        'url': f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{token.id}',
    }

    return details


def create_token_for_contact(contact, customer_response):
    """
    Generate new token and set all existing unexpired token to expire
    """
    CustomerResponseToken.objects.filter(
        company_contact=contact,
        customer_response=customer_response,
        expires_on__gte=datetime.utcnow()).update(expires_on=datetime.utcnow())
    expires_on = datetime.utcnow() + timedelta(days=7)
    new_token = CustomerResponseToken.objects.create(
        expires_on=expires_on,
        company_contact=contact,
        customer_response=customer_response,
    )
    return new_token
