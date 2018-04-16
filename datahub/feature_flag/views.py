from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datahub.feature_flag.models import FeatureFlag


@api_view()
@permission_classes([IsAuthenticated])
def get_feature_flags(request):
    """Return a dictionary of feature flags."""
    feature_flags = {
        feature_flag.code: feature_flag.is_active
        for feature_flag in FeatureFlag.objects.all()
    }
    return Response(data=feature_flags)
