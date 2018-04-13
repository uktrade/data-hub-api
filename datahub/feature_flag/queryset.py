from datahub.feature_flag.models import FeatureFlag


def get_feature_flag_queryset():
    """Gets the feature flag query set used by v3 views."""
    return FeatureFlag.objects.all()
