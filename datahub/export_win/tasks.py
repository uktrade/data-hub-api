from django.conf import settings


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
