from ...models import InteractionPermission


NON_RESTRICTED_READ_PERMISSIONS = (
    (
        InteractionPermission.read_all,
    ),
    (
        InteractionPermission.read_all,
        InteractionPermission.read_associated_investmentproject,
    )
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        InteractionPermission.change_all,
    ),
    (
        InteractionPermission.change_all,
        InteractionPermission.change_associated_investmentproject,
    )
)


def resolve_data(data):
    """
    Given a data dict with keys and values,
    if a value is a callable, it resolves it
    if a value is an object with a 'pk' attribute, it uses that instead.

    It returns a new dict with resolved values.
    """
    def resolve_value(value):
        if callable(value):
            resolved_value = value()
        else:
            resolved_value = value

        if hasattr(resolved_value, 'pk'):
            obj_value = resolved_value
            resolved_value = {
                'id': str(obj_value.id),
                'name': obj_value.name
            }

            # this is here because of inconsistent endpoint :(
            if hasattr(obj_value, 'project_code'):
                resolved_value['project_code'] = obj_value.project_code
        return resolved_value

    return {key: resolve_value(value) for key, value in data.items()}
