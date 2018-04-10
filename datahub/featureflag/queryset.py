from datahub.featureflag.models import FeatureFlag


def get_featureflag_queryset():
    """Gets the feature flag query set used by v3 views."""
    return FeatureFlag.objects.select_related(
        'created_by',
        'modified_by',
    )
