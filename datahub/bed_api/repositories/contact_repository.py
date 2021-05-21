from simple_salesforce import format_soql

from datahub.bed_api.constants import ContactQuery
from datahub.bed_api.repositories.salesforce_repository import SalesforceRepository


class ContactRepository(SalesforceRepository):
    """
    Repository pattern for Salesforce interactions with Contacts data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/FieldsAndRelationships/view
    """

    def add(self, data):
        """
        Add a new Contact using a POST
        :param data: A dict of Contact data
        :return: Returns New Contact
        """
        return self.salesforce.Contact.create(data)

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Contact.delete(record_id)

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier
        :param record_id: Unique identifier value, associated with Id value typically
        :return: True if it exists and False if it does not
        """
        response = self.query(
            format_soql(
                ContactQuery.get_by_id.value.sql,
                id=record_id,
            ),
        )
        return self.exists_status(record_id, response)

    def get(self, record_id):
        """
        Get single item by identifier
        :param record_id: Unique identifier value
        :return: Result of Contact get by id
        """
        return self.salesforce.Contact.get(record_id)

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: Contact record or None
        """
        return self.salesforce.Contact.get_by_custom_id(
            custom_id_field,
            custom_id_value,
        )

    def update(self, record_id, data):
        """
        Update Contact
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated
        """
        return self.salesforce.Contact.update(record_id, data)
