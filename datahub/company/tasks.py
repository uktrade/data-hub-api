import uuid

from celery import shared_task
from dateutil import parser
from django.utils.timezone import is_aware, make_naive
from raven.contrib.django.raven_compat.models import client, settings

from datahub.korben.connector import KorbenConnector


def handle_time(timestamp):
    """Return a naive datime object adjusted on the timezone."""
    if timestamp is None:
        return timestamp
    time = parser.parse(timestamp)
    return make_naive(time, timezone=time.tzinfo) if is_aware(time) else time


@shared_task(bind=True)
def save_to_korben(self, data, user_id, db_table, update):
    """Save to Korben."""
    from datahub.core.models import TaskInfo
    # We are generating a random task id if the task has not one
    # this should only happen when this function is called directly instead of going through a queue
    # it's BAD but we only call this function directly in the tests
    # we are abusing the request task id, and any other solution tried didn't work
    task_id = self.request.id or uuid.uuid4()
    task_info, _ = TaskInfo.objects.get_or_create(
        task_id=task_id,
        defaults=dict(
            user_id=user_id,
            changes=data,
            db_table=db_table,
            update=update
        )
    )
    try:
        korben_connector = KorbenConnector()
        remote_object = korben_connector.get(
            data=data,
            table_name=db_table
        )
        cdms_time = handle_time(remote_object.json().get('modified_on'))
        object_time = handle_time(data['modified_on'])
        if cdms_time is None or (cdms_time <= object_time):
            korben_connector.post(
                table_name=db_table,
                data=data,
                update=update
            )
        # We want to retry on any exception because we don't want to lose user changes!!
        else:
            task_info.note = 'Stale object, not saved.'
            task_info.save()
    except Exception as e:
        client.captureException()
        raise self.retry(
            exc=e,
            countdown=int(self.request.retries * self.request.retries),
            max_retries=settings.TASK_MAX_RETRIES,
        )
