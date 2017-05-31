import uuid

from colander import Invalid, null, SchemaType


class RelationshipType(SchemaType):
    """Define a relationship type in colander."""

    def __init__(self, typename):
        """Define the typename."""
        self.typename = typename

    def serialize(self, node, appstruct):
        """Serialize data checking for typename."""
        if appstruct is null:
            return null
        appstruct = dict(appstruct)
        if 'data' not in appstruct:
            raise Invalid(node, f'{appstruct!r} has no key data')
        if 'type' not in appstruct['data']:
            raise Invalid(node, f'{appstruct!r} has no key type')
        appstruct_type = appstruct['data']['type']
        if appstruct_type != self.typename:
            raise Invalid(node, f'type {appstruct_type} should be '
                                f'{self.typename}')
        return appstruct and 'true' or 'false'

    def deserialize(self, node, cstruct):
        """Deserialize data.

        {'data': None}
        {'data': {'type': 'foo', 'id: 1}}
        """
        if cstruct is null:
            return null
        cstruct = dict(cstruct)
        if 'data' not in cstruct:
            raise Invalid(node, f'{cstruct!r} has no key data')
        if cstruct['data']:
            if 'type' not in cstruct['data']:
                raise Invalid(node, f'{cstruct!r} has no key type')
            if 'id' not in cstruct['data']:
                raise Invalid(node, f'{cstruct!r} has no key id')
            cstruct_type = cstruct['data']['type']
            if cstruct_type != self.typename:
                raise Invalid(node, f'type {cstruct_type} should be '
                                    f'{self.typename}')
            cstruct['data']['id'] = uuid.UUID(cstruct['data']['id'])
        return cstruct


class IsExactly:
    """Validator to check an exact value is passed."""

    def __init__(self, check_value):
        """Take the check value."""
        self.check_value = check_value

    def __call__(self, node, value):
        """Take the actual value to be checked."""
        if not value == self.check_value:
            raise Invalid(node, f'Value must be {self.check_value}')
