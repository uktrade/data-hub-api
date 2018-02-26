import reversion
from reversion.middleware import RevisionMiddleware

EXCLUDED_BASE_MODEL_FIELDS = ('created_on', 'created_by', 'modified_on', 'modified_by')


def register_base_model(extra_exclude=None, **kwargs):
    """
    Shortcut to reversion.register() which excludes some fields defined on BaseModel
    by default.

    These aren't particularly useful to save in django-reversion versions because
    created_by/created_on will not change between versions, and modified_on/modified_by
    is tracked by django-reversion separately in revisions.

    :param extra_exclude: list of "extra" fields to exclude along with the default ones
    :param kwargs: same as the reversion.register ones

    Note: if you pass `exclude` you override the default excluded fields. You cannot use
        exclude and extra_exclude at the same time as they are mutual exclusive.

    Note: if you remove this decorator from a model, VersionAdmin must be removed
    as well otherwise the model will be auto-registered automatically.
    """
    assert 'exclude' not in kwargs or not extra_exclude, (
        "You can't pass in extra_exclude and exclude at the same time."
    )

    if 'exclude' not in kwargs:
        kwargs['exclude'] = (
            *EXCLUDED_BASE_MODEL_FIELDS,
            *(extra_exclude or ())
        )

    return reversion.register(**kwargs)


class NonAtomicRevisionMiddleware(RevisionMiddleware):
    """
    Same as reversion.middleware.RevisionMiddleware but with atomic == False.
    Therefore the resulting atomic value depends on:
    - the `ATOMIC_REQUESTS` settings
    - whether `transaction.atomic()` is used
    - whether `transaction.non_atomic_requests()` is used
    """

    atomic = False
