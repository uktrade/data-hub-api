import uuid

from celery import shared_task
from dateutil import parser
from django.utils.timezone import is_aware, make_naive
from raven.contrib.django.raven_compat.models import client, settings

from datahub.korben.connector import KorbenConnector


def handle_time(timestamp):
    """Return a naive datime object adjusted on the timezone."""
    time = parser.parse(timestamp)
    if is_aware(time):
        return make_naive(time, timezone=time.tzinfo)
    else:
        return time


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
            changes=data,
            db_table=db_table,
            update=update
        )
    )
    korben_connector = KorbenConnector()
    remote_object = korben_connector.get(
        data=data,
        table_name=db_table
    )
    cdms_time = handle_time(remote_object.json()['modified_on'])
    object_time = handle_time(data['modified_on'])
    if cdms_time <= object_time:
        try:
            korben_connector.post(
                table_name=db_table,
                data=data,
                update=update
            )
        # We want to retry on any exception because we don't want to lose user changes!!
        except Exception as e:
            client.captureException()
            raise self.retry(
                exc=e,
                countdown=int(self.request.retries * self.request.retries),
                max_retries=settings.TASK_MAX_RETRIES,
            )
    else:
        task_info.note = 'Stale object, not saved.'
        task_info.save()
