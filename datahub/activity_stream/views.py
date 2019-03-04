from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from config.settings.types import HawkScope
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)


class ActivityStreamViewSet(HawkResponseSigningMixin, ViewSet):
    """List-only view set for the activity stream."""

    authentication_classes = (HawkAuthentication,)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.activity_stream

    def list(self, request):
        """A single page of activities"""
        return Response({'secret': 'content-for-pen-test'})
