from datahub.bed_api.repositories.base_repository import ReadWriteRepository


class EventRepository(ReadWriteRepository):
    """
    Event Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Event or Interaction data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/FieldsAndRelationships/view
    """

    entity_name = 'Event__c'
