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
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'documents.SharePointDocument'


class UploadableDocumentFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=20)
    original_filename = factory.Faker('file_path')
    document = factory.SubFactory(DocumentFactory)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'documents.UploadableDocument'


class CompanySharePointDocumentFactory(factory.django.DjangoModelFactory):
    """Generates a GenericDocument instance linking a Company to a SharePointDocument."""

    document = factory.SubFactory(SharePointDocumentFactory)
    related_object = factory.SubFactory(CompanyFactory)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    archived = False

    class Meta:
        model = 'documents.GenericDocument'

    @factory.post_generation
    def sync_created_and_modified_on_document_instance(obj, create, extracted, **kwargs):  # noqa
        obj.document.created_by = obj.created_by
        obj.document.modified_by = obj.modified_by
        obj.document.created_on = obj.created_on
        obj.document.modified_on = obj.modified_on
        obj.document.save()


class CompanyUploadableDocumentFactory(factory.django.DjangoModelFactory):
    """Generates a GenericDocument instance linking a Company to an UploadableDocument."""

    document = factory.SubFactory(UploadableDocumentFactory)
    related_object = factory.SubFactory(CompanyFactory)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    archived = False

    class Meta:
        model = 'documents.GenericDocument'

    @factory.post_generation
    def sync_created_and_modified_on_document_instance(obj, create, extracted, **kwargs):  # noqa
        obj.document.created_by = obj.created_by
        obj.document.modified_by = obj.modified_by
        obj.document.created_on = obj.created_on
        obj.document.modified_on = obj.modified_on
        obj.document.save()
