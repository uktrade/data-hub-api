from datahub.bed_api.constants import EventQuery
from datahub.bed_api.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):
    """
    Event Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Event or Interaction data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/FieldsAndRelationships/view
    """

    entity_name = 'Event__c'
    entity_query = EventQuery
