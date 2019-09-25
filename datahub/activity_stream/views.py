from config.settings.types import HawkScope
from datahub.core.auth import PaaSIPAuthentication
from datahub.core.hawk_receiver import (
    HawkAuthentication,
    HawkResponseSigningMixin,
    HawkScopePermission,
)
from datahub.core.viewsets import CoreViewSet


class ActivityViewSet(HawkResponseSigningMixin, CoreViewSet):
    """
    Generic view for activities.

    Sets up authentication, permission and scope.
    """

    authentication_classes = (PaaSIPAuthentication, HawkAuthentication)
    permission_classes = (HawkScopePermission,)
    required_hawk_scope = HawkScope.activity_stream
