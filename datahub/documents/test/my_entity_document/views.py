"""Document test views."""
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticated

from datahub.documents.test.my_entity_document.models import MyEntityDocument
from datahub.documents.test.my_entity_document.serializers import MyEntityDocumentSerializer
from datahub.documents.views import BaseEntityDocumentModelViewSet


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    permission_classes = (IsAuthenticated,)
    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
