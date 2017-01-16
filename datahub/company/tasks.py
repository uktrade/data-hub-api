import uuid

from celery import shared_task
from dateutil import parser
from django.apps import apps
from django.utils.timezone import make_naive
from raven.contrib.django.raven_compat.models import client, settings
from requests import RequestException

from datahub.korben.connector import KorbenConnector
from datahub.korben.exceptions import KorbenException


@shared_task(bind=True)
def save_to_korben(self, object_id, user_id, db_table, update):
    """Save to Korben."""
    from datahub.core.models import TaskInfo
    model_name = db_table.replace('_', '.')
    model_class = apps.get_model(model_name)
    object_to_save = model_class.objects.get(pk=object_id)
    name = 'Saving {0} to CDMS.'.format(str(object_to_save))
    # We are generating a random task id if the task has not one
    # this should only happen when this function is called directly instead of going through a queue
    # it's BAD but we only call this function directly in the tests
    # we are abusing the request task id, and any other solution tried didn't work
    task_id = self.request.id or uuid.uuid4()
    task_info, _ = TaskInfo.objects.get_or_create(
        task_id=task_id,
        defaults=dict(
            user_id=user_id,
            name=name
        )
    )
    # korben_connector = KorbenConnector()
    # data = object_to_save.convert_model_to_korben_format()
    # remote_object = korben_connector.get(
    #     data=data,
    #     table_name=db_table
    # )
    # cdms_time = parser.parse(remote_object.json()['modified_on'])
    # if make_naive(cdms_time) <= object_to_save.modified_on:
    try:
        object_to_save.save_to_korben(update)
    except (KorbenException, RequestException) as e:
        client.captureException()
        raise self.retry(
            exc=e,
            countdown=settings.TASK_RETRY_DELAY_SECONDS,
            max_retries=settings.TASK_MAX_RETRIES,
        )
    # else:
    #     itask_info.note = 'Stale object, not saved.'
    #     task_info.save()
