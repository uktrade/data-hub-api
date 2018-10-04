"""Document test views."""
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.documents.test.my_entity_document.models import MyEntityDocument
from datahub.documents.test.my_entity_document.serializers import MyEntityDocumentSerializer
from datahub.documents.views import BaseEntityDocumentModelViewSet
from datahub.oauth.scopes import Scope


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
