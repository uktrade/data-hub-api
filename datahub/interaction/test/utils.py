from datahub.core.test_utils import random_obj_for_queryset
from datahub.metadata.models import Service


def random_service(disabled=False):
    """Get a random service."""
    # TODO: services that require interaction questions need to be excluded until the support
    # is fully implemented otherwise some tests, which don't provide answers when required, will
    # fail
    return random_obj_for_queryset(
        Service.objects.filter(
            disabled_on__isnull=not disabled,
            interaction_questions__isnull=True,
            children__isnull=True,
        ),
    )
