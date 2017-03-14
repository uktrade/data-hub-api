import colander


class RelationshipDataSchema(colander.MappingSchema):
    type = colander.SchemaNode(colander.String())
    id = colander.SchemaNode(colander.String())


class RelationshipSchema(colander.MappingSchema):
    data = RelationshipDataSchema()


class Status(RelationshipSchema):
    pass


class Company(RelationshipSchema):
    pass


class Contact(RelationshipSchema):
    pass


class Service(RelationshipSchema):
    pass


class DITTeam(RelationshipSchema):
    pass


class UKRegion(RelationshipSchema):
    pass


class Sector(RelationshipSchema):
    pass


class CountryOfInterest(RelationshipSchema):
    pass


class Event(RelationshipSchema):
    pass


def create_relationship_entity_schema(type_name):
    data_schema = colander.MappingSchema()
    data_schema.add(colander.String()


class ServiceDeliveryAttributes(colander.MappingSchema):

    subject = colander.SchemaNode(colander.String())
    date = colander.SchemaNode(colander.DateTime())
    notes = colander.SchemaNode(colander.String())
    feedback = colander.SchemaNode(colander.String())


class ServiceDeliveryRelationships(colander.MappingSchema):

    status = Status()
    company = Company()
    contact = Contact()
    service = Service()
    dit_team = DITTeam()
    uk_region = UKRegion()
    sector = Sector()
    country_of_interest = CountryOfInterest()
    event = Event()


class ServiceDeliverySchema(colander.Schema):
    type = colander.SchemaNode(colander.String())
    attributes = ServiceDeliveryAttributes()
    relationships = ServiceDeliveryRelationships()
