from datahub.bed_api.constants import EventAttendeeQuery
from datahub.bed_api.repositories.base_repository import BaseRepository


class EventAttendeeRepository(BaseRepository):
    """
    Event Attendee Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Event Attendee data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAX/FieldsAndRelationships/view
    """

    entity_name = 'Event_Attendee__c'
    entity_query = EventAttendeeQuery
