"""This module contains the temporary code that will be replaced by the Korben client."""

from django.conf import settings

from core.utils import model_to_dictionary
from .utils import get_elasticsearch_client


def save_model(model_instance, update=False):
    """Add or update data to ES."""
    client = get_elasticsearch_client()
    data = model_to_dictionary(model_instance)
    doc_type = model_instance._meta.db_table

    object_id = data.pop('id')
    if update:
        client.update(
            index=settings.ES_INDEX,
            doc_type=doc_type,
            body={'doc': data},
            id=object_id,
            refresh=True
        )
    else:
        client.create(
            index=settings.ES_INDEX,
            doc_type=doc_type,
            body=data,
            id=object_id,
            refresh=True
        )


def document_exists(client, doc_type, document_id):
    """Check whether the document with a specific ID exists."""

    return client.exists(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        id=document_id,
        realtime=True
    )
