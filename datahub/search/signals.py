from logging import getLogger

from datahub.core.utils import submit_to_thread_pool
from datahub.search import elasticsearch

logger = getLogger(__name__)


def _sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    instance = db_model.objects.get(pk=pk)
    doc = search_model.es_document(instance)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)


def sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    return submit_to_thread_pool(_sync_es, search_model, db_model, pk)
