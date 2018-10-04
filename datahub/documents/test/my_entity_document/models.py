from django.conf import settings
from django.db import models
from django.urls import reverse

from datahub.documents.models import AbstractEntityDocumentModel

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class MyEntityDocument(AbstractEntityDocumentModel):
    """Simple entity document model."""

    my_field = models.CharField(max_length=MAX_LENGTH)

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            'test-document-item-download',
            kwargs={
                'entity_document_pk': self.pk,
            },
        )
