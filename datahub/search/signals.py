from logging import getLogger

from raven.contrib.django.raven_compat.models import client

from datahub.core.utils import executor
from datahub.search import elasticsearch

logger = getLogger(__name__)


def _sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    try:
        instance = db_model.objects.get(pk=pk)
        doc = search_model.es_document(instance)
        elasticsearch.bulk(actions=(doc, ), chunk_size=1)
    except:  # noqa: B901
        logger.exception('Error while saving entity to ES')
        client.captureException()
        raise


def sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    return executor.submit(_sync_es, search_model, db_model, pk)
