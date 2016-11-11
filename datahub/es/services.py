"""This module contains the temporary code that will be replaced by the Korben client."""

from django.conf import settings


def document_exists(client, doc_type, document_id):
    """Check whether the document with a specific ID exists."""

    return client.exists(
        index=settings.ES_INDEX,
        doc_type=doc_type,
        id=document_id,
        realtime=True
    )
