from simple_salesforce import format_soql, Salesforce

from datahub.bed_api.constants import (
    AccountQuery,
    ContactQuery,
    EventAttendeeQuery,
    EventQuery,
)


class SalesforceRepository:
    """
    Base Salesforce Repository to encapsulate default CRUD operations
    for interacting with Salesforce API
    """

    def __init__(self, salesforce: Salesforce):
        """
        Salesforce
        :param salesforce:
        """
        self.salesforce = salesforce

    def add(self, data):
        """
        Creates a new SObject using a POST
        :param data: A dict of the data to create the SObject from
        :return: Raises NotImplementedError
        """
        raise NotImplementedError

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Record id for deleting data
        :return: Raises NotImplementedError
        """
        raise NotImplementedError

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier and
        the most efficient mechanism for checking ie the least content
        with ideally a head verb
        :param record_id: Unique identifier value, associated with Id value typically
        :return: Raises NotImplementedError
        """
        raise NotImplementedError

    def get(self, record_id):
        """
        Get a single item by unique identifier
        :param record_id: Unique identifier value
        :return: Raises NotImplementedError
        """
        raise NotImplementedError

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: Raises NotImplementedError
        """
        raise NotImplementedError

    def query(self, query, include_deleted=False, **kwargs):
        """
        Return the result of a Salesforce SOQL query as a dict decoded from
        the Salesforce response JSON payload.
        See https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/
        soql_sosl/sforce_api_calls_soql_select.htm for more details.
        :param query: Salesforce SQL query
        :param include_deleted: Include records marker for deletion
        :param kwargs: Where filter arguments
        :return: Salesforce SOQL query
        """
        return self.salesforce.query(query, include_deleted, **kwargs)

    def query_next(
        self,
        next_records_identifier,
        identifier_is_url=False,
        include_deleted=False,
        **kwargs,
    ):
        """
        Retrieves next or more results from a query that returned more results
        than the batch maximum
        :param next_records_identifier: Either the Id of the next Salesforce
                                     object in the result, or a URL to the
                                     next record in the result
        :param identifier_is_url: True if `next_records_identifier` should be
                               treated as a URL, False if
                               `next_records_identifier` should be treated as
                               an Id
        :param include_deleted: True if the `next_records_identifier` refers to a
                             query that includes deleted records. Only used if
                             `identifier_is_url` is False
        :param kwargs: Filters or where clause attributes
        :return: Returns a dict decoded from the Salesforce
        """
        return self.salesforce.query_more(
            next_records_identifier,
            identifier_is_url,
            include_deleted,
            **kwargs,
        )

    def update(self, record_id, data):
        """
        Update based on some unique identifier
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Returns NotImplementedError
        """
        raise NotImplementedError

    def exists_status(self, record_id, response) -> bool:
        """
        Check if a record exists by the response
        :param record_id: Unique identifier
        :param response: Response returned from query by id
        :return: True if response assigned, totalSize is
        greater than 1 and there is a record id the equivalent of that value
        """
        return (
            response is not None
            and response['totalSize'] >= 1
            and response['done'] is True
            and len(response['records']) > 0
            and response['records'][0].get('Id') == record_id
        )


class ContactRepository(SalesforceRepository):
    """
    Repository pattern for Salesforce interactions with Contacts data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/FieldsAndRelationships/view
    """

    def __init__(self, salesforce: Salesforce):
        """
        Constructor
        :param salesforce: Simple Salesforce representing session information
        """
        super().__init__(salesforce=salesforce)

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


class AccountRepository(SalesforceRepository):
    """
    Repository pattern for Salesforce interactions with Account data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Account/FieldsAndRelationships/view
    """

    def __init__(self, salesforce: Salesforce):
        """
        Constructor
        :param salesforce: Simple Salesforce representing session information
        """
        super().__init__(salesforce=salesforce)

    def add(self, data):
        """
        Add a new Account using a POST
        :param data: A dict of Account data
        :return: Returns New Account
        """
        return self.salesforce.Account.create(data)

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Account.delete(record_id)

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier
        :param record_id: Unique identifier value, associated with Id value typically
        :return: True if it exists and False if it does not
        """
        response = self.query(
            format_soql(
                AccountQuery.get_by_id.value.sql,
                id=record_id,
            ),
        )
        return self.exists_status(record_id, response)

    def get(self, record_id):
        """
        Get single item by identifier
        :param record_id: Unique identifier value
        :return:
        """
        return self.salesforce.Account.get(record_id)

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: Account record or None
        """
        return self.salesforce.Account.get_by_custom_id(
            custom_id_field,
            custom_id_value,
        )

    def update(self, record_id, data):
        """
        Update Account
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated Account
        """
        return self.salesforce.Account.update(record_id, data)


class EventRepository(SalesforceRepository):
    """
    Repository pattern for Salesforce interactions with Event or Interaction data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/FieldsAndRelationships/view
    """

    def __init__(self, salesforce: Salesforce):
        """
        Constructor
        :param salesforce: Simple Salesforce representing session information
        """
        super().__init__(salesforce=salesforce)

    def add(self, data):
        """
        Add a new Event using a POST
        :param data: A dict of Event data
        :return: Returns New Account
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
        :return:
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


class EventAttendeeRepository(SalesforceRepository):
    """
    Repository pattern for Salesforce interactions with Event Attendee data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAX/FieldsAndRelationships/view
    """

    def __init__(self, salesforce: Salesforce):
        """
        Constructor
        :param salesforce: Simple Salesforce representing session information
        """
        super().__init__(salesforce=salesforce)

    def add(self, data):
        """
        Add a new Event Attendee using a POST
        :param data: A dict of Event data
        :return: Returns New Account
        """
        return self.salesforce.Event_Attendee__c.create(data)

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Event_Attendee__c.delete(record_id)

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier
        :param record_id: Unique identifier value, associated with Id value typically
        :return: True if it exists and False if it does not
        """
        response = self.query(
            format_soql(
                EventAttendeeQuery.get_by_id.value.sql,
                id=record_id,
            ),
        )
        return self.exists_status(record_id, response)

    def get(self, record_id):
        """
        Get single item by identifier
        :param record_id: Unique identifier value
        :return:
        """
        return self.salesforce.Event_Attendee__c.get(record_id)

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: Event record or None
        """
        return self.salesforce.Event_Attendee__c.get_by_custom_id(
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
        return self.salesforce.Event_Attendee__c.update(record_id, data)
