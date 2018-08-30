from .models import FeatureFlag


def is_feature_flag_active(code):
    """
    Tells if given feature flag is active.

    If feature flag doesn't exist, it returns False.
    """
    try:
        feature_flag = FeatureFlag.objects.get(code=code)
    except FeatureFlag.DoesNotExist:
        return False

    return feature_flag.is_active
