from enum import Enum

from django.conf import settings

from datahub.company.constants import NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_by_email


# TODO: Remove this module once the D&B investigations endpoint has been released
class Template(Enum):
    """
    GOV.UK notifications template ids.
    """

    request_new_business_record = '6b987540-82c3-47ea-86b8-dacdd26410c4'


def notify_new_dnb_investigation(company):
    """
    Notify DNB of a new company investigation.
    """
    if not is_feature_flag_active(NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG):
        return
    investigation_context = get_dnb_investigation_context(company)
    recipients = settings.DNB_INVESTIGATION_NOTIFICATION_RECIPIENTS
    for email_address in recipients:
        notify_by_email(
            email_address,
            Template.request_new_business_record.value,
            investigation_context,
            notify_service_name=NotifyServiceName.dnb_investigation,
        )


def get_dnb_investigation_context(company):
    """
    Get a dict with values for fields that are to be sent
    to DNB for investigation.
    """
    address_parts = [
        company.address_1,
        company.address_2,
        company.address_town,
        company.address_county,
        company.address_country.name,
        company.address_postcode,
    ]
    dnb_investigation_data = company.dnb_investigation_data or {}
    return {
        'business_name': company.name,
        'business_address': ', '.join(
            address_part for address_part in address_parts if address_part
        ),
        'website': company.website or '',
        'contact_number': dnb_investigation_data.get('telephone_number') or '',
    }
