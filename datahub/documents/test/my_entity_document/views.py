"""Document test views."""
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.oauth.scopes import Scope
from .models import MyEntityDocument
from .serializers import MyEntityDocumentSerializer
from ...views import BaseEntityDocumentModelViewSet


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
