from django.utils.decorators import decorator_from_middleware
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkScopePermission,
    HawkResponseMiddleware,
)
from datahub.core.test.support.models import MultiAddressModel, MyDisableableModel, PermissionModel
from datahub.core.test.support.serializers import (
    MultiAddressModelSerializer,
    MyDisableableModelSerializer,
    PermissionModelSerializer,
)
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.test.scopes import TestScope


class MyDisableableModelViewset(CoreViewSet):
    """MyDisableableModel view set."""

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (TestScope.test_scope_1,)
    serializer_class = MyDisableableModelSerializer
    queryset = MyDisableableModel.objects.all()


class PermissionModelViewset(CoreViewSet):
    """PermissionModel view set."""

    serializer_class = PermissionModelSerializer
    required_scopes = ()
    queryset = PermissionModel.objects.all()


class MultiAddressModelViewset(CoreViewSet):
    """MultiAddressModel view set."""

    permission_classes = []
    serializer_class = MultiAddressModelSerializer
    queryset = MultiAddressModel.objects.all()


class HawkView(APIView):
    """View using Hawk authentication."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = next(iter(HawkScope.__members__.values()))

    @decorator_from_middleware(HawkResponseMiddleware)
    def get(self, request):
        """Simple test view with fixed response"""
        return Response({'content': 'hawk-test-view'})
