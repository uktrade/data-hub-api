from rest_framework.permissions import IsAuthenticated

from datahub.core.viewsets import CoreViewSetV3
from datahub.feature_flag.models import FeatureFlag
from datahub.feature_flag.serializers import FeatureFlagSerializer


class FeatureFlagViewSet(CoreViewSetV3):
    """Feature flag ViewSet v3."""

    pagination_class = None
    permission_classes = (IsAuthenticated,)
    queryset = FeatureFlag.objects.all()
    serializer_class = FeatureFlagSerializer
