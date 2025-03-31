import pytest
from django.contrib.contenttypes.models import ContentType

from datahub.company.test.factories import CompanyFactory
from datahub.documents.models import GenericDocument
from datahub.documents.serializers import (
    GenericDocumentRetrieveSerializer,
    SharePointDocumentSerializer,
)
from datahub.documents.test.factories import (
    CompanySharePointDocumentFactory,
    SharePointDocumentFactory,
)
from datahub.documents.test.test_utils import (
    assert_retrieved_generic_document,
    assert_retrieved_sharepoint_document,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory

pytestmark = pytest.mark.django_db


class TestSharePointDocumentSerializer:
    """Tests for SharePointDocumentSerializer."""

    def test_serializing_instance_returns_expected_fields(self):
        sharepoint_document = SharePointDocumentFactory()
        serializer = SharePointDocumentSerializer(sharepoint_document)
        assert_retrieved_sharepoint_document(sharepoint_document, serializer.data)


class TestGenericDocumentRetrieveSerializer:
    """Tests for GenericDocumentRetrieveSerializer."""

    def test_serializing_instance_returns_expected_fields(self):
        generic_document = CompanySharePointDocumentFactory()
        serializer = GenericDocumentRetrieveSerializer(generic_document)
        assert_retrieved_generic_document(generic_document, serializer.data)

    def test_serializer_raises_error_if_unsupported_document_type(self):
        unsupported_document = CompanySharePointDocumentFactory()
        unsupported_document_type = ContentType.objects.get_for_model(unsupported_document)

        company = CompanyFactory()
        company_type = ContentType.objects.get_for_model(company)

        generic_document = GenericDocument.objects.create(
            document_type=unsupported_document_type,
            document_object_id=unsupported_document.id,
            related_object_type=company_type,
            related_object_id=company.id,
        )
        with pytest.raises(Exception):
            serializer = GenericDocumentRetrieveSerializer(generic_document)
            serializer.data  # noqa: B018

    def test_serializer_raises_error_if_unsupported_related_object_type(self):
        document = SharePointDocumentFactory()
        document_type = ContentType.objects.get_for_model(document)

        unsupported_related_object = InvestmentProjectFactory()
        unsupported_related_object_type = ContentType.objects.get_for_model(
            unsupported_related_object,
        )

        generic_document = GenericDocument.objects.create(
            document_type=document_type,
            document_object_id=document.id,
            related_object_type=unsupported_related_object_type,
            related_object_id=unsupported_related_object.id,
        )
        with pytest.raises(Exception):
            serializer = GenericDocumentRetrieveSerializer(generic_document)
            serializer.data  # noqa: B018
