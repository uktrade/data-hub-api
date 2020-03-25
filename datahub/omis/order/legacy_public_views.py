from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.core.viewsets import CoreViewSet
from datahub.oauth.scopes import Scope
from datahub.omis.order.models import Order
from datahub.omis.order.serializers import PublicOrderSerializer


class LegacyPublicOrderViewSet(CoreViewSet):
    """ViewSet for legacy public facing order endpoint."""

    lookup_field = 'public_token'

    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    required_scopes = (Scope.public_omis_front_end,)
    serializer_class = PublicOrderSerializer
    queryset = Order.objects.publicly_accessible(
        include_reopened=True,
    ).select_related(
        'company',
        'contact',
    )
