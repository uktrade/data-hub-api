from django.template.response import TemplateResponse
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings.types import HawkScope
from datahub.core.admin import max_upload_size
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.test.support.models import MultiAddressModel, MyDisableableModel, PermissionModel
from datahub.core.test.support.serializers import (
    MultiAddressModelSerializer,
    MyDisableableModelSerializer,
    PermissionModelSerializer,
)
from datahub.core.viewsets import CoreViewSet
from datahub.oauth.test.scopes import TestScope

MAX_UPLOAD_SIZE = 50


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


class HawkViewWithoutScope(HawkResponseSigningMixin, APIView):
    """View using Hawk authentication."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = ()

    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'hawk-test-view-without-scope'})


class HawkViewWithScope(HawkResponseSigningMixin, APIView):
    """View using Hawk authentication."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = next(iter(HawkScope.__members__.values()))

    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'hawk-test-view-with-scope'})


class PaasIPView(APIView):
    """View using PaaS IP Authentication."""

    authentication_classes = (PaaSIPAuthentication,)
    permission_classes = ()

    def get(self, request):
        """Simple test view with fixed response."""
        return Response({'content': 'paas-ip-test-view'})


@max_upload_size(MAX_UPLOAD_SIZE)
def max_upload_size_view(request):
    """View for testing upload file size limiting."""
    # Force files to be processed
    request.FILES
    return TemplateResponse(request, 'empty.html')
