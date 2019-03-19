from collections.abc import Mapping, Sequence

from datahub.core.test_utils import create_test_user
from datahub.interaction.models import InteractionPermission


def resolve_data(data):
    """
    Given a value:

    - if it's a callable, it resolves it
    - if it's an object with a 'pk' attribute, it uses that instead
    - if it's a sequence it resolves each of the sequence's values
    - if it's a dict it resolves each value of the dict

    The resolved value is returned.
    """
    if isinstance(data, Sequence) and not isinstance(data, str):
        return [resolve_data(item) for item in data]

    if isinstance(data, Mapping):
        return {key: resolve_data(value) for key, value in data.items()}

    return _resolve_single_value(data)


def _resolve_single_value(value):
    if callable(value):
        resolved_value = value()
    else:
        resolved_value = value

    if hasattr(resolved_value, 'pk'):
        obj_value = resolved_value
        resolved_value = {
            'id': str(obj_value.id),
            'name': obj_value.name,
        }

        # this is here because of inconsistent endpoint :(
        if hasattr(obj_value, 'project_code'):
            resolved_value['project_code'] = obj_value.project_code
    return resolved_value


def create_restricted_investment_project_user():
    """
    Creates a user with access to only interactions for investment projects that they are
    associated with (non-investment-project interaction cannot be accessed).
    """
    return create_test_user(
        permission_codenames=[
            InteractionPermission.view_associated_investmentproject,
            InteractionPermission.add_associated_investmentproject,
            InteractionPermission.change_associated_investmentproject,
        ],
    )
