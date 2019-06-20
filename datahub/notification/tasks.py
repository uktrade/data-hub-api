from celery import shared_task

from datahub.notification.core import client


@shared_task(acks_late=True, priority=9)
def send_email_notification(
    recipient_email,
    template_identifier,
    context=None,
):
    """
    Celery task to call the notify API to send a templated email notification
    to an email address.
    """
    client.send_email_notification(recipient_email, template_identifier, context)
