from config.settings.types import HawkScope
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

    authentication_classes = (HawkAuthentication, )
    permission_classes = (HawkScopePermission, )
    required_hawk_scope = HawkScope.activity_stream
