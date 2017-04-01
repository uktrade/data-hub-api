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
            raise Invalid(node, '%r has no key data' % appstruct)
        if 'type' not in appstruct['data']:
            raise Invalid(node, '%r has no key type' % appstruct)
        if appstruct['data']['type'] != self.typename:
            raise Invalid(node, 'type %s should be %s' % (
                appstruct['data']['type'], self.typename))
        return appstruct and 'true' or 'false'

    def deserialize(self, node, cstruct):
        """Deserialize data."""
        if cstruct is null:
            return null
        cstruct = dict(cstruct)
        if 'data' not in cstruct:
            raise Invalid(node, '%r has no key data' % cstruct)
        if 'type' not in cstruct['data']:
            raise Invalid(node, '%r has no key type' % cstruct)
        if cstruct['data']['type'] != self.typename:
            raise Invalid(node, 'type %s should be %s' % (
                cstruct['data']['type'], self.typename))
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
            raise Invalid(node, 'Value must be {value}'.format(value=self.check_value))
