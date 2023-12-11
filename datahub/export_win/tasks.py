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
    # set existing unexpired token to expire (if there is)
    if has_unexpired_token_for_contact(contact):
        existing_tokens = CustomerResponseToken.objects.filter(
            company_contact=contact,
            customer_response=customer_response,
            expires_on__gt=datetime.utcnow(),
        )
        for existing_token in existing_tokens:
            existing_token.expires_on = datetime.utcnow()
            existing_token.save()
    # create a new token
    expires_on = datetime.utcnow() + timedelta(days=7)
    new_token = CustomerResponseToken.objects.create(
        expires_on=expires_on,
        company_contact=contact,
        customer_response=customer_response,
    )
    return new_token


def has_unexpired_token_for_contact(contact):
    now = datetime.utcnow()
    unexpired_token_exists = CustomerResponseToken.objects.filter(
        company_contact__id=contact.id,
        expires_on__gt=now,
    ).exists()
    return unexpired_token_exists
