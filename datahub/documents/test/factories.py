from datetime import timezone

import factory

from datahub.company.test.factories import AdviserFactory
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
