import uuid

from celery import shared_task
from raven.contrib.django.raven_compat.models import client, settings
from requests import RequestException

from datahub.korben.connector import KorbenConnector
from datahub.korben.exceptions import KorbenException


@shared_task(bind=True)
def save_to_korben(self, data, user_id, db_table, update):
    """Save to Korben."""
    from datahub.core.models import TaskInfo
    name = 'Saving to CDMS.'
    # We are generating a random task id if the task has not one
    # this should only happen when this function is called directly instead of going through a queue
    # it's BAD but we only call this function directly in the tests
    # we are abusing the request task id, and any other solution tried didn't work
    task_id = self.request.id or uuid.uuid4()
    task_info, _ = TaskInfo.objects.get_or_create(
        task_id=task_id,
        defaults=dict(
            user_id=user_id,
            name=name,
            changes=data
        )
    )
    korben_connector = KorbenConnector()
    try:
        korben_connector.post(
            table_name=db_table,
            data=data,
            update=update
        )
    except (KorbenException, RequestException) as e:
        client.captureException()
        raise self.retry(
            exc=e,
            countdown=settings.TASK_RETRY_DELAY_SECONDS,
            max_retries=settings.TASK_MAX_RETRIES,
        )
