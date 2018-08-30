from .models import FeatureFlag


def is_feature_flag_active(code):
    """
    Tells if given feature flag is active.

    If feature flag doesn't exist, it returns False.
    """
    return FeatureFlag.objects.filter(code=code, is_active=True).exists()
