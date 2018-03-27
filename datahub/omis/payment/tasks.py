from datetime import timedelta

from celery.task import task
from django.db import transaction
from django.utils.timezone import now

from .models import PaymentGatewaySession


@task(ignore_result=True)
def refresh_payment_gateway_session(session_id):
    """
    Celery task that refreshes the session with id `session_id`.

    Note: there's no retry setting as we don't want to retry in case of
    exceptions. This is because the next periodic run of
    `refresh_pending_payment_gateway_sessions` will trigger this task
    again and in the meantime sentry errors can be analysed.

    :param session_id: id of the payment gateway session to refresh.
    """
    with transaction.atomic():
        qs = PaymentGatewaySession.objects.filter(pk=session_id)
        session = qs.select_for_update().first()
        session.refresh_from_govuk_payment()


@task(ignore_result=True)
def refresh_pending_payment_gateway_sessions(age_check=60, refresh_rate=0.5):
    """
    Celery task that refreshes old ongoing payments in case something
    happens during the payment journey or the user abandons the payment
    session.

    :param age_check: minutes since the session was last modified to be
        included in the query. E.g. age_check=60 means that only ongoing
        sessions 1-hour old are refreshed.
        This is to give time to the user to complete the journey normally.
    :param refresh_rate: delay in seconds between each refresh subtasks
        to avoid hitting GOV.UK Pay too hard.
    """
    dt_check = now() - timedelta(minutes=age_check)
    qs = PaymentGatewaySession.objects.ongoing()
    session_ids = qs.filter(modified_on__lte=dt_check).values_list('id', flat=True)

    for index, session_id in enumerate(session_ids):
        refresh_payment_gateway_session.apply_async(
            args=(session_id, ),
            countdown=(refresh_rate * index)
        )
