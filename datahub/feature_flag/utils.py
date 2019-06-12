from functools import wraps

from django.db.models import Exists
from django.http import Http404

from datahub.feature_flag.models import FeatureFlag


def is_feature_flag_active(code):
    """
    Tells if given feature flag is active.

    If feature flag doesn't exist, it returns False.
    """
    return FeatureFlag.objects.filter(code=code, is_active=True).exists()


def build_is_feature_flag_active_subquery(code):
    """Return a subquery that checks if a feature flag is active."""
    return Exists(
        FeatureFlag.objects.filter(code=code, is_active=True),
    )


def feature_flagged_view(code):
    """
    Decorator to put a view behind a feature flag.

    This returns a 404 is a specified feature flag is not active. Otherwise, the view is called
    normally.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not is_feature_flag_active(code):
                raise Http404

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
