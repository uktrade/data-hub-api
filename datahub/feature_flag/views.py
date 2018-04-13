from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from datahub.core.viewsets import CoreViewSetV3
from datahub.feature_flag.queryset import get_feature_flag_queryset
from datahub.feature_flag.serializers import FeatureFlagSerializer
from datahub.oauth.scopes import Scope


class FeatureFlagViewSet(CoreViewSetV3):
    """Feature flag ViewSet v3."""

    required_scopes = (Scope.internal_front_end,)
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
    serializer_class = FeatureFlagSerializer
    queryset = get_feature_flag_queryset()
