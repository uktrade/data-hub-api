from simple_salesforce import format_soql

from datahub.bed_api.constants import EventQuery
from datahub.bed_api.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):
    """
    Repository pattern for Salesforce interactions with Event or Interaction data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/FieldsAndRelationships/view
    """

    def add(self, data):
        """
        Add a new Event using a POST
        :param data: A dict of Event data
        :return: Returns Event
        """
        return self.salesforce.Event__c.create(data)

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Event__c.delete(record_id)

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier
        :param record_id: Unique identifier value, associated with Id value typically
        :return: True if it exists and False if it does not
        """
        response = self.query(
            format_soql(
                EventQuery.get_by_id.value.sql,
                id=record_id,
            ),
        )
        return self.exists_status(record_id, response)

    def get(self, record_id):
        """
        Get single item by identifier
        :param record_id: Unique identifier value
        :return: Result of Event get by id
        """
        return self.salesforce.Event__c.get(record_id)

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: Event record or None
        """
        return self.salesforce.Event__c.get_by_custom_id(
            custom_id_field,
            custom_id_value,
        )

    def update(self, record_id, data):
        """
        Update Event
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated Event
        """
        return self.salesforce.Event__c.update(record_id, data)
