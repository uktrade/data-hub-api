from datahub.core.test_utils import create_test_user, resolve_objects
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
    return resolve_objects(data, object_resolver=_resolve_model_object)


def _resolve_model_object(obj):
    resolved_value = {
        'id': str(obj.id),
        'name': obj.name,
    }

    # this is here because of inconsistent endpoint :(
    if hasattr(obj, 'project_code'):
        resolved_value['project_code'] = obj.project_code

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
