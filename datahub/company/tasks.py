import logging

from celery import shared_task
from dateutil import parser
from django.utils.timezone import is_aware, make_naive
from raven.contrib.django.raven_compat.models import client, settings

from datahub.core.utils import log_and_ignore_exceptions
from datahub.korben.connector import KorbenConnector


logger = logging.getLogger(__name__)


def handle_time(timestamp):
    """Return a naive datime object adjusted on the timezone."""
    if timestamp is None:
        return timestamp
    time = parser.parse(timestamp)
    return make_naive(time, timezone=time.tzinfo) if is_aware(time) else time


@shared_task(bind=True, default_retry_delay=30 * 60, rate_limit='60/m')
def save_to_korben(self, data, user_id, db_table, update):
    """Save to Korben."""
    _ = user_id  # noqa: F841; user is needed for signal handling, before_task_publish signal expects it to be there
    try:
        korben_connector = KorbenConnector()
        remote_object = korben_connector.get(
            data=data,
            table_name=db_table
        )
        if remote_object.status_code == 404:
            # Sync discrepancy create instead of update
            update = False

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
        with log_and_ignore_exceptions():
            client.captureException()

        raise self.retry(
            exc=e,
            countdown=int(self.request.retries * self.request.retries),
            max_retries=settings.TASK_MAX_RETRIES,
        )
