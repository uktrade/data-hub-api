import pytest

from datahub.documents.serializers import (
    GenericDocumentRetrieveSerializer,
    SharePointDocumentSerializer,
)
from datahub.documents.test.factories import (
    CompanySharePointDocumentFactory,
    SharePointDocumentFactory,
)
from datahub.documents.utils import (
    assert_retrieved_generic_document,
    assert_retrieved_sharepoint_document,
)


pytestmark = pytest.mark.django_db


class TestSharePointDocumentSerializer:
    """Tests for SharePointDocumentSerializer"""

    def test_serializing_instance_returns_expected_fields(self):
        sharepoint_document = SharePointDocumentFactory()
        serializer = SharePointDocumentSerializer(sharepoint_document)
        assert_retrieved_sharepoint_document(sharepoint_document, serializer.data)


class TestGenericDocumentRetrieveSerializer:
    """Tests for GenericDocumentRetrieveSerializer"""

    def test_serializing_instance_returns_expected_fields(self):
        generic_document = CompanySharePointDocumentFactory()
        serializer = GenericDocumentRetrieveSerializer(generic_document)
        assert_retrieved_generic_document(generic_document, serializer.data)
