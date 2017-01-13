from celery import shared_task
from dateutil import parser
from django.apps import apps
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
    task_info, _ = TaskInfo.objects.get_or_create(
        task_id=self.request.id,
        defaults=dict(
            user_id=user_id,
            name=name
        )
    )
    korben_connector = KorbenConnector()
    data = object_to_save.convert_model_to_korben_format()
    remote_object = korben_connector.get(
        data=data,
        table_name=db_table
    )
    if parser.parse(remote_object['modified_on']) <= object_to_save.modified_on:
        try:
            object_to_save.save_to_korben(update)
        except (KorbenException, RequestException) as e:
            client.captureException()
            raise self.retry(
                exc=e,
                countdown=settings.TASK_RETRY_DELAY_SECONDS,
                max_retries=settings.TASK_MAX_RETRIES,
            )
