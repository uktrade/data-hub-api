"""This module contains the temporary code that will be replaced by the Korben client."""

from django.conf import settings
from django.db.models import ForeignKey

from es.utils import get_elasticsearch_client


def from_model_to_es_document(model_instance):
    """Convert a model instance to ES document, expanding FKs."""

    data = {}
    for field in model_instance._meta.fields:
        if isinstance(field, ForeignKey):
            data[field.name] = getattr(model_instance, field.name).name
        else:
            data[field.name] = getattr(model_instance, field.name)
    return data


def write_to_es(client, doc_type, data):
    """Add or Update to ES."""

    client.create(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        body=data,
        id=data['id'],
        refresh=True
    )


def save_model(model_instance):
    """Add new data to ES."""
    client = get_elasticsearch_client()
    data = from_model_to_es_document(model_instance)
    write_to_es(client, model_instance._meta.db_table, data)


def update_model(model_instance):
    client = get_elasticsearch_client()
    data = from_model_to_es_document(model_instance)
    write_to_es(client, model_instance._meta.db_table, data)


def delete_model(model_instance):
    client = get_elasticsearch_client()
    data = from_model_to_es_document(model_instance)
    data['archived'] = True
    write_to_es(client, model_instance._meta.db_table, data)

