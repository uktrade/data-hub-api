

from datetime import datetime, timedelta
from logging import getLogger

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.export_win.constants import (
    ANONYMOUS,
    EMAIL_MAX_DAYS_TO_RESPONSE_THRESHOLD,
    EMAIL_MAX_TOKEN_ISSUED_WITHIN_RESPONSE_THRESHOLD,
    EMAIL_MAX_WEEKS_AUTO_RESEND_THRESHOLD,
)
from datahub.export_win.models import Breakdown, CustomerResponse, CustomerResponseToken
from datahub.notification.constants import NotifyServiceName
from datahub.notification.core import notify_gateway
from datahub.reminder.models import EmailDeliveryStatus

logger = getLogger(__name__)


def auto_resend_client_email_from_unconfirmed_win():
    with advisory_lock(
        'auto_resend_client_email_from_unconfirmed_win',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Unconfirmed export win checks from customer response are already being '
                'processed by another worker.',
            )
            return

        current_date = datetime.utcnow()
        win_max_days_threshold = \
            EMAIL_MAX_DAYS_TO_RESPONSE_THRESHOLD * EMAIL_MAX_WEEKS_AUTO_RESEND_THRESHOLD

        win_maturity_days_threshold = current_date - timedelta(days=win_max_days_threshold + 1)

        win_email_response_threshold = \
            current_date - timedelta(days=EMAIL_MAX_DAYS_TO_RESPONSE_THRESHOLD - 1)

        customer_responses = (
            CustomerResponse.objects.filter(
                agree_with_win__isnull=True,
                created_on__gte=win_maturity_days_threshold,
            )
            .annotate(num_tokens=Count('tokens'))
            .filter(num_tokens__lt=EMAIL_MAX_TOKEN_ISSUED_WITHIN_RESPONSE_THRESHOLD)
            .exclude(tokens__created_on__gt=win_email_response_threshold)
        )

        logger.info(
            'auto_resend_client_email_from_unconfirmed_win attempting to resend unconfirmed '
            f'wins, with {len(customer_responses)} of line(s)',
        )

        for customer_response in customer_responses:
            win = customer_response.win
            company_contacts = win.company_contacts

            for company_contact in company_contacts.all():
                token = create_token_for_contact(
                    company_contact,
                    customer_response,
                )
                context = get_all_fields_for_client_email_receipt(
                    token,
                    customer_response,
                )
                template_id = settings.EXPORT_WIN_CLIENT_RECEIPT_TEMPLATE_ID
                notify_export_win_email_by_rq_email(
                    company_contact.email,
                    template_id,
                    context,
                    update_customer_response_token_for_email_notification_id,
                    token.id,
                )


def create_token_for_contact(contact, customer_response, adviser=None):
    """Generate new token and set all existing unexpired token to expire.
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
        adviser=adviser,
    )
    return new_token


def get_all_fields_for_client_email_receipt(token, customer_response):
    win = customer_response.win
    details = {
        'country_destination': win.country.name,
        'lead_officer_name': win.lead_officer.name,
        'goods_services': win.goods_vs_services.name,
        'url': f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{token.id}',
    }

    if token.company_contact:
        win_token = token.company_contact
        details.update({
            'customer_email': win_token.email,
            'client_firstname': win_token.first_name,
        })

    if token.adviser:
        win_token = token.adviser
        details.update({
            'customer_email': win_token.contact_email,
            'client_firstname': win_token.first_name,
        })

    return details


def _get_customer_details_for_lead_officer_email(customer_response):
    win = customer_response.win
    contact = win.company_contacts.first()
    contact_name = contact.name if contact else ANONYMOUS
    if win.company:
        client_company_name = win.company.name
        url = settings.EXPORT_WIN_LEAD_OFFICER_REVIEW_WIN_URL.format(
            company_id=win.company.id,
            uuid=win.id,
        )
    else:
        client_company_name = ANONYMOUS
        url = settings.DATAHUB_FRONTEND_BASE_URL
    return {
        'client_fullname': contact_name,
        'client_company_name': client_company_name,
        'url': url,
    }


def get_all_fields_for_lead_officer_email_receipt_no(customer_response):
    win = customer_response.win
    details = {
        'lead_officer_email': win.lead_officer.contact_email,
        'country_destination': win.country.name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'goods_services': win.goods_vs_services.name,
        **_get_customer_details_for_lead_officer_email(customer_response),
    }
    return details


def get_all_fields_for_lead_officer_email_receipt_yes(customer_response):
    win = customer_response.win
    total_export_win_value = Breakdown.objects.filter(win=win).aggregate(
        Sum('value'))['value__sum'] or 0
    details = {
        'lead_officer_email': win.lead_officer.contact_email,
        'country_destination': win.country.name,
        'lead_officer_first_name': win.lead_officer.first_name,
        'total_export_win_value': total_export_win_value,
        'goods_services': win.goods_vs_services.name,
        **_get_customer_details_for_lead_officer_email(customer_response),
    }
    return details


def notify_export_win_email_by_rq_email(
        email_address,
        template_identifier,
        context,
        update_task,
        token_id=None,
):
    """Notify Export win contact, using GOVUK notify and some template context.
    """
    job = job_scheduler(
        function=send_export_win_email_notification_via_rq,
        function_args=(
            email_address,
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
        object_id=None,
        notify_service_name=None,
):
    """Email notification function to be scheduled by RQ,
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
            object_id,
        ),
        queue_name=LONG_RUNNING_QUEUE,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )

    logger.info(
        'Task send_export_win_email_notification_via_rq completed '
        f'email_notification_id to {response["id"]} and object_id set to {object_id}',
    )

    return response['id'], object_id


def update_customer_response_token_for_email_notification_id(email_notification_id, object_id):
    token = CustomerResponseToken.objects.get(id=object_id)
    token.email_notification_id = email_notification_id
    token.save()

    logger.info(
        'Task update_customer_response_token_email_status completed '
        f'email_response_status to {email_notification_id} and customer_response_token_id '
        f'set to {object_id}',
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


def update_customer_response_for_lead_officer_notification_id(
    email_notification_id,
    object_id,
):
    customer_response = CustomerResponse.objects.get(id=object_id)
    customer_response.lead_officer_email_notification_id = email_notification_id
    customer_response.lead_officer_email_sent_on = datetime.utcnow()
    customer_response.save(
        update_fields=('lead_officer_email_notification_id', 'lead_officer_email_sent_on'),
    )

    logger.info(
        'Task update_customer_response_for_lead_officer_notification_id completed '
        f'email_response_status to {email_notification_id} and customer_response_id '
        f'set to {object_id}',
    )


def update_notify_email_delivery_status_for_customer_response():
    with advisory_lock(
        'update_notify_email_delivery_status_for_customer_response',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for customer response are already being '
                'processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)
        notification_ids = (
            CustomerResponse.objects.filter(
                Q(lead_officer_email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(lead_officer_email_delivery_status=EmailDeliveryStatus.SENDING),
                lead_officer_email_sent_on__gte=date_threshold,
                lead_officer_email_notification_id__isnull=False,
            )
            .values_list('lead_officer_email_notification_id', flat=True)
            .distinct()
        )

        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.export_win,
            )
            if 'status' in result:
                CustomerResponse.objects.filter(
                    lead_officer_email_notification_id=notification_id,
                ).update(
                    lead_officer_email_delivery_status=result['status'],
                )
