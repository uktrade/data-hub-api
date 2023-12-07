from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum

from datahub.export_win.models import Breakdown

from datahub.export_win.models import CustomerResponseToken
from logging import getLogger

from django.conf import settings
from django.db.models import Sum

from datahub.export_win.models import Breakdown

from datahub.export_win.models import CustomerResponseToken


def get_all_fields_for_client_email_receipt(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    details = {
        'customer_email': win_token.email,
        'country_destination': win.country,
        'client_firstname': win_token.first_name,
        'lead_officer_name': win.lead_officer.name,
        'goods_services': win.goods_vs_services.name,
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


def get_all_fields_for_lead_officer_email_receipt_no(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    details = {
        'lead_officer_email': win.lead_officer.email,
        'country_destination': win.country,
        'client_fullname': win_token.first_name + ' ' + win_token.last_name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'goods_services': win.goods_vs_services.name,
        'client_company_name': win_token.company.name,
        'url': settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(uuid=win.id),
    }

    return details


def get_all_fields_for_lead_officer_email_receipt_yes(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    total_export_win_value = Breakdown.objects.filter(win=win).aggregate(
        Sum('value'))['value__sum'] or 0
    details = {
        'lead_officer_email': win.lead_officer.email,
        'country_destination': win.country,
        'client_fullname': win_token.first_name + ' ' + win_token.last_name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'total_export_win_value': total_export_win_value,
        'goods_services': win.goods_vs_services.name,
        'client_company_name': win_token.company.name,
        'url': settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(uuid=win.id),
    }

    return details
