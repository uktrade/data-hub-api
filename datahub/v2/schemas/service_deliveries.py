"""Schemas."""

import colander
from django.conf import settings

from .utils import IsExactly, RelationshipType


class ServiceDeliveryAttributes(colander.MappingSchema):
    """Colander schema for service deliveries attributes."""

    subject = colander.SchemaNode(colander.String())
    date = colander.SchemaNode(colander.DateTime())
    notes = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=settings.CDMS_TEXT_MAX_LENGTH)
    )
    feedback = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=settings.CDMS_TEXT_MAX_LENGTH),
        missing=colander.null
    )


class ServiceDeliveryRelationships(colander.MappingSchema):
    """Colander schema for service deliveries relationships."""

    status = colander.SchemaNode(RelationshipType(typename='ServiceDeliveryStatus'))
    company = colander.SchemaNode(RelationshipType(typename='Company'))
    contact = colander.SchemaNode(RelationshipType(typename='Contact'))
    service = colander.SchemaNode(RelationshipType(typename='Service'))
    dit_team = colander.SchemaNode(RelationshipType(typename='Team'))
    dit_adviser = colander.SchemaNode(RelationshipType(typename='Adviser'))
    sector = colander.SchemaNode(
        RelationshipType(typename='Sector'),
        missing=colander.null
    )
    uk_region = colander.SchemaNode(
        RelationshipType(typename='UKRegion'),
        missing=colander.null)
    country_of_interest = colander.SchemaNode(
        RelationshipType(typename='Country'),
        missing=colander.null)
    event = colander.SchemaNode(
        RelationshipType(typename='Event'),
        missing=colander.null)
    service_offer = colander.SchemaNode(
        RelationshipType(typename='ServiceOffer'),
        missing=colander.null)


class ServiceDeliverySchema(colander.Schema):
    """Colander schema for service deliveries."""

    type = colander.SchemaNode(
        colander.String(),
        validator=IsExactly('ServiceDelivery')
    )
    id = colander.SchemaNode(
        colander.String(),
        validator=colander.uuid,
        missing=colander.null
    )
    attributes = ServiceDeliveryAttributes()
    relationships = ServiceDeliveryRelationships()
