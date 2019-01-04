from collections.abc import Sequence

from datahub.core.test_utils import create_test_user
from datahub.interaction.models import InteractionPermission


def resolve_data(data):
    """
    Given a data dict with keys and values,
    if a value is a callable, it resolves it
    if a value is an object with a 'pk' attribute, it uses that instead.

    It returns a new dict with resolved values.
    """
    return {key: _resolve_value(value) for key, value in data.items()}


def _resolve_value(value):
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_resolve_single_value(item) for item in value]

    return _resolve_single_value(value)


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
