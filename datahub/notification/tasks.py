from celery import shared_task

from datahub.notification.core import notify_gateway


@shared_task(
    acks_late=True,
    priority=9,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=60,
)
def send_email_notification(
    recipient_email,
    template_identifier,
    context=None,
    notify_service_name=None,
):
    """
    Celery task to call the notify API to send a templated email notification
    to an email address.
    """
    response = notify_gateway.send_email_notification(
        recipient_email,
        template_identifier,
        context,
        notify_service_name,
    )
    return response['id']
