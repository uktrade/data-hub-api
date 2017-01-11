from celery import shared_task
from django.apps import apps
from raven.contrib.django.raven_compat.models import client
from requests import RequestException

from datahub.korben.connector import KorbenConnector
from datahub.korben.exceptions import KorbenException


@shared_task(bind=True)
def save_to_korben(self, object_id, model_name, update):
    """Save to Korben."""
    korben_connector = KorbenConnector()
    model_class = apps.get_model(model_name)
    #remote_object = korben_connector.get()
    object_to_save = model_class.objects.get(pk=object_id)

    try:
        korben_response = object_to_save.save_to_korben(update)
    except (KorbenException, RequestException) as e:
        client.captureException()
        raise self.retry(exc=e)
