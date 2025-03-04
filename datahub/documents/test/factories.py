from datetime import timezone

import factory

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
)
from datahub.documents.models import UploadStatus


class DocumentFactory(factory.django.DjangoModelFactory):
    """Document factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    bucket_id = 'default'
    path = factory.Sequence(lambda n: f'projects/doc{n}.txt')
    uploaded_on = factory.Faker('past_datetime', tzinfo=timezone.utc)
    scan_initiated_on = None
    scanned_on = None
    av_clean = None
    av_reason = ''
    status = UploadStatus.NOT_VIRUS_SCANNED

    class Meta:
        model = 'documents.Document'


class SharePointDocumentFactory(factory.django.DjangoModelFactory):

    title = factory.Faker('text', max_nb_chars=20)
    url = factory.Faker('url')

    class Meta:
        model = 'documents.SharePointDocument'


class CompanySharePointDocumentFactory(factory.django.DjangoModelFactory):
    """Generates a GenericDocument instance linking a Company to a SharePointDocument."""

    document = factory.SubFactory(SharePointDocumentFactory)
    related_object = factory.SubFactory(CompanyFactory)
    archived = False

    class Meta:
        model = 'documents.GenericDocument'
