

from datetime import datetime, timedelta

from logging import getLogger

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.db.models import (Q, Sum)
from django.utils.timezone import now

from django_pglocks import advisory_lock

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.export_win.models import (Breakdown, CustomerResponseToken)
from datahub.notification.constants import NotifyServiceName
from datahub.notification.core import notify_gateway
from datahub.reminder.models import EmailDeliveryStatus

logger = getLogger(__name__)


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


def get_all_fields_for_client_email_receipt(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    details = {
        'customer_email': win_token.email,
        'country_destination': win.country.name,
        'client_firstname': win_token.first_name,
        'lead_officer_name': win.lead_officer.name,
        'goods_services': win.goods_vs_services.name,
        'url': f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{token.id}',
    }

    return details


def get_all_fields_for_lead_officer_email_receipt_no(token, customer_response):
    win = customer_response.win
    win_token = token.company_contact
    details = {
        'lead_officer_email': win.lead_officer.email,
        'country_destination': win.country.name,
        'client_fullname': win_token.first_name + ' ' + win_token.last_name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'goods_services': win.goods_vs_services.name,
        'client_company_name': win_token.company.name,
        'url': settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(uuid=win.id),
    }

    return details


def get_all_fields_for_lead_officer_email_receipt_yes(token, customer_response):
    win = customer_response.win
    company_contact = token.company_contact
    total_export_win_value = Breakdown.objects.filter(win=win).aggregate(
        Sum('value'))['value__sum'] or 0
    details = {
        'lead_officer_email': win.lead_officer.email,
        'country_destination': win.country.name,
        'client_fullname': company_contact.name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'total_export_win_value': total_export_win_value,
        'goods_services': win.goods_vs_services.name,
        'client_company_name': company_contact.company.name,
        'url': settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(uuid=win.id),
    }

    return details


def notify_export_win_contact_by_rq_email(
        contact_email_address,
        template_identifier,
        context,
        update_task,
        token_id=None,
):
    """
    Notify Export win contact, using GOVUK notify and some template context.
    """
    job = job_scheduler(
        function=send_export_win_email_notification_via_rq,
        function_args=(
            contact_email_address,
            template_identifier,
            context,
            update_task,
            token_id,
            NotifyServiceName.export_win,
        ),
        retry_backoff=True,
        max_retries=5,
    )

    return job


def send_export_win_email_notification_via_rq(
        recipient_email,
        template_identifier,
        context=None,
        update_delivery_status_task=None,
        token_id=None,
        notify_service_name=None,
):
    """
    Email notification function to be scheduled by RQ,
    setting up a second task to update the email delivery status.

    Logged notification_id and response so it is possible to track the status of
    email delivery.
    """
    logger.info(
        'send_export_win_email_notification_via_rq attempting to send email '
        f'to recipient {recipient_email}, using template identifier {template_identifier}',
    )
    response = notify_gateway.send_email_notification(
        recipient_email,
        template_identifier,
        context,
        notify_service_name,
    )

    logger.info(
        f'send_export_win_email_notification_via_rq email sent to recipient {recipient_email}, '
        f'received response {response}',
    )

    job_scheduler(
        function=update_delivery_status_task,
        function_args=(
            response['id'],
            token_id,
        ),
        queue_name=LONG_RUNNING_QUEUE,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )

    logger.info(
        'Task send_export_win_email_notification_via_rq completed '
        f'email_notification_id to {response["id"]} and token_id set to {token_id}',
    )

    return response['id'], token_id


def update_customer_response_token_for_email_notification_id(email_notification_id, token_id):
    token = CustomerResponseToken.objects.get(id=token_id)
    token.email_notification_id = email_notification_id
    token.save()

    logger.info(
        'Task update_customer_response_token_email_status completed '
        f'email_response_status to {email_notification_id} and customer_response_id '
        f'set to {token_id}',
    )


def update_notify_email_delivery_status_for_customer_response_token():
    with advisory_lock(
        'update_notify_email_delivery_status_for_customer_response_token',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for customer response token are already being '
                'processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)
        notification_ids = (
            CustomerResponseToken.objects.filter(
                Q(email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(email_delivery_status=EmailDeliveryStatus.SENDING),
                created_on__gte=date_threshold,
                email_notification_id__isnull=False,
            )
            .values_list('email_notification_id', flat=True)
            .distinct()
        )

        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.export_win,
            )
            if 'status' in result:
                CustomerResponseToken.objects.filter(
                    email_notification_id=notification_id,
                ).update(
                    email_delivery_status=result['status'],
                )
