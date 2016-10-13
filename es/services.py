"""This module contains the temporary code that will be replaced by the Korben client."""

from django.conf import settings
from django.db.models import ForeignKey

from .utils import get_elasticsearch_client


def from_model_to_es_document(model_instance):
    """Convert a model instance to ES document, expanding FKs."""

    data = {}
    for field in model_instance._meta.fields:
        if isinstance(field, ForeignKey):
            field_value = getattr(model_instance, field.name)
            data[field.name] = field_value.name if field_value else None
        else:
            data[field.name] = getattr(model_instance, field.name)
    return data


def write_to_es(client, doc_type, data):
    """Add or Update to ES.

    Because we force feed an ID to the Django model we can't differentiate between object creation and object update
    https://docs.djangoproject.com/en/1.10/ref/models/instances/#how-django-knows-to-update-vs-insert

    As temporary solution we perform a check on ES to see if the document with the give ID already exists.
    """
    # we pop the ID out because the dynamic mappings creates this field as long, while we use UUID
    # need a way to force this type in the mapping

    object_id = data.pop('id')
    if document_exists(client, doc_type, object_id):
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


def save_model(model_instance):
    """Add new data to ES."""
    client = get_elasticsearch_client()
    data = from_model_to_es_document(model_instance)
    write_to_es(client, model_instance._meta.db_table, data)


def document_exists(client, doc_type, document_id):
    """Check whether the document with a specific ID exists."""

    return client.exists(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        id=document_id,
        realtime=True
    )
