from notifications_python_client.errors import HTTPError
from rq import get_current_job

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE

from datahub.notification.core import notify_gateway


def schedule_send_email_notification(
    recipient_email,
    template_identifier,
    context=None,
    notify_service_name=None,
    *args,
    **kwargs,
):
    """
    Task to schedule send_email_notification with RQ.
    """
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=send_email_notification,
        function_kwargs={
            'recipient_email': recipient_email,
            'template_identifier': template_identifier,
            'context': context,
            'notify_service_name': notify_service_name,
        },
        max_retries=5,
    )
    return job


def send_email_notification(
    recipient_email,
    template_identifier,
    context=None,
    notify_service_name=None,
):
    """
    Call the notify API to send a templated email notification
    to an email address.
    To schedule with RQ call schedule_send_email_notification(...)
    """
    try:
        response = notify_gateway.send_email_notification(
            recipient_email,
            template_identifier,
            context,
            notify_service_name,
        )
    except HTTPError as exc:
        # Raise 400/403 responses without retry when called from  RQ - these are problems with the
        # way we are calling the notify service and retries will not result in
        # a successful outcome.
        if exc.status_code in (400, 403):
            # get current job from RQ when called from scheduler and reset.
            job = get_current_job()
            if job is not None:
                job.retries_left = 0
        raise
    return response['id']
