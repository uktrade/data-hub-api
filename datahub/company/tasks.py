import logging

from celery import shared_task
from celery.signals import before_task_publish
from dateutil import parser
from django.utils.timezone import is_aware, make_naive
from raven.contrib.django.raven_compat.models import client, settings

from datahub.korben.connector import KorbenConnector


logger = logging.getLogger(__name__)


def handle_time(timestamp):
    """Return a naive datime object adjusted on the timezone."""
    if timestamp is None:
        return timestamp
    time = parser.parse(timestamp)
    return make_naive(time, timezone=time.tzinfo) if is_aware(time) else time


@shared_task(bind=True)
def save_to_korben(self, data, user_id, db_table, update):
    """Save to Korben."""
    _ = user_id  # noqa: F841; user is needed for signal handling, before_task_publish signal expects it to be there
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
        else:
            logger.warning(
                'Stale object ID: {id} '
                'datahub time: {dhtime} CDMS time: {cdmstime}'.format(
                    id=data['id'],
                    dhtime=object_time.isoformat(),
                    cdmstime=cdms_time.isoformat(),
                )
            )

    except Exception as e:
        try:
            client.captureException()
        except:  # noqa: B901;
            logger.exception('Sentry fails...')
        finally:
            raise self.retry(
                exc=e,
                countdown=int(self.request.retries * self.request.retries),
                max_retries=settings.TASK_MAX_RETRIES,
            )


@before_task_publish.connect(sender='datahub.company.tasks.save_to_korben')
def create_task_info(sender=None, headers=None, body=None, **kwargs):
    """Create TaskInfo meta object for rerun and audit trail."""
    from datahub.core.models import TaskInfo

    _, task_kwargs, _ = body

    task_info = TaskInfo(
        task_id=headers['id'],
        changes=task_kwargs['data'],
        user_id=task_kwargs['user_id'],
        db_table=task_kwargs['db_table'],
        update=task_kwargs['update'],
    )
    task_info.save()
