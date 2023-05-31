from functools import wraps

from django.http import Http404

from datahub.feature_flag.models import FeatureFlag


def is_feature_flag_active(code):
    """
    Tells if given feature flag is active.

    If feature flag doesn't exist, it returns False.
    """
    return FeatureFlag.objects.filter(code=code, is_active=True).exists()


def is_user_feature_flag_active(code, user):
    """
    Tells if given user feature flag is active for the specified user.

    If user feature flag doesn't exist, it returns False.
    """
    params = {
        'code': code,
        'is_active': True,
    }

    return any([
        *[
            feature_group.features.filter(**params).exists()
            for feature_group in user.feature_groups.filter(is_active=True)
        ],
        user.features.filter(**params).exists(),
    ])


def is_user_feature_flag_group_active(code, user):
    """
    Tells if given user feature flag group is active for the specified user.

    If user feature flag group doesn't exist, it returns False.
    """
    return user.feature_groups.filter(code=code, is_active=True).exists()


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
