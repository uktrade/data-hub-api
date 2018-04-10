from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope
from rest_framework.filters import OrderingFilter

from datahub.core.viewsets import CoreViewSetV3
from datahub.featureflag.queryset import get_featureflag_queryset
from datahub.featureflag.serializers import FeatureFlagSerializer
from datahub.oauth.scopes import Scope


class FeatureFlagViewSet(CoreViewSetV3):
    """Feature flag ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    serializer_class = FeatureFlagSerializer
    queryset = get_featureflag_queryset()
    filter_backends = (
        OrderingFilter,
    )
    ordering_fields = ('created_on',)
    ordering = ('-created_on',)
