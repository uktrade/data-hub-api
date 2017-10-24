from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.core.viewsets import CoreViewSetV3
from datahub.oauth.test.scopes import TestScope
from .models import MyDisableableModel
from .serializers import MyDisableableModelSerializer


class MyDisableableModelViewset(CoreViewSetV3):
    """MyDisableableModel view set."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (TestScope.test_scope_1,)
    serializer_class = MyDisableableModelSerializer
    queryset = MyDisableableModel.objects.all()
