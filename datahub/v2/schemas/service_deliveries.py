"""Schemas."""

import colander

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
        return False


class ServiceDeliveryAttributes(colander.MappingSchema):
    """Colander schema for service deliveries attributes."""

    id = colander.SchemaNode(colander.String())
    subject = colander.SchemaNode(colander.String())
    date = colander.SchemaNode(colander.DateTime())
    notes = colander.SchemaNode(colander.String())
    feedback = colander.SchemaNode(colander.String())


class ServiceDeliveryRelationships(colander.MappingSchema):
    """Colander schema for service deliveries relationships."""

    status = colander.SchemaNode(RelationshipType(typename='Status'))
    company = colander.SchemaNode(RelationshipType(typename='Company'))
    contact = colander.SchemaNode(RelationshipType(typename='Contact'))
    service = colander.SchemaNode(RelationshipType(typename='Service'))
    dit_team = colander.SchemaNode(RelationshipType(typename='Team'))
    uk_region = colander.SchemaNode(RelationshipType(typename='UKRegion'))
    sector = colander.SchemaNode(RelationshipType(typename='Sector'))
    country_of_interest = colander.SchemaNode(RelationshipType(typename='Country'))
    event = colander.SchemaNode(RelationshipType(typename='Event'))


class ServiceDeliverySchema(colander.Schema):
    """Colander schema for service deliveries."""

    type = colander.SchemaNode(colander.String())
    attributes = ServiceDeliveryAttributes()
    relationships = ServiceDeliveryRelationships()
