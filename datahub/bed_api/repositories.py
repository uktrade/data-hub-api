from simple_salesforce import format_soql, Salesforce


class ReadRepository:
    """
    Base Salesforce Repository to encapsulate dealing with
    reading Salesforce data only
    """

    entity_name = None

    def __init__(self, salesforce: Salesforce):
        """
        Initialise Repository

        :param salesforce: Authenticated Salesforce instance
        """
        self.salesforce = salesforce

    def get(self, record_id):
        """
        Get a single item by unique identifier

        :param record_id: Unique identifier value

        :return: Fetched Salesforce Object
        """
        return getattr(self.salesforce, self.entity_name).get(record_id)

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier and
        the most efficient mechanism for checking ie the least content
        with ideally a head verb

        :param record_id: Unique identifier value, associated with Id value typically
        :raises: NotImplementedError
        """
        query = f'SELECT Id FROM {self.entity_name} WHERE Id = {{id}}'
        response = self.query(format_soql(query, id=record_id))
        return (
            response is not None
            and response['totalSize'] > 0
            and len(response['records']) > 0
            and response['records'][0].get('Id') == record_id
        )

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field

        :param custom_id_field: API name of a custom field that was defined
            as an External ID
        :param custom_id_value: External ID value

        :return: Return data by custom id
        """
        return getattr(self.salesforce, self.entity_name).get_by_custom_id(
            custom_id_field,
            custom_id_value,
        )

    def get_by_datahub_id(self, datahub_id_value):
        """
        Returns the result of a GET by datahub identifier value

        :param datahub_id_value: External ID value

        :return: Return data by datahub id
        """
        return self.get_by('Datahub_ID__c', datahub_id_value)

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
            object in the result, or a URL to the next record in the result
        :param identifier_is_url: True if `next_records_identifier` should be
            treated as a URL, False if `next_records_identifier` should be
            treated as an Id
        :param include_deleted: True if the `next_records_identifier` refers to
            a query that includes deleted records. Only used if
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


class ReadWriteRepository(ReadRepository):
    """
    Base Salesforce Repository to encapsulate dealing with
    reading and writing Salesforce Data
    """

    def add(self, data):
        """
        Creates a new SObject

        :param data: A dict of the data to create the SObject from

        :return: New Salesforce Object
        """
        return getattr(self.salesforce, self.entity_name).create(data)

    def update(self, record_id, data):
        """
        Update based on some unique identifier

        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:

        :return: Updated Salesforce Object
        """
        return getattr(self.salesforce, self.entity_name).update(record_id, data)

    def delete(self, record_id):
        """
        Delete a single item by unique identifier

        :param record_id: Record id for deleting data

        :returns: Delete result
        """
        return getattr(self.salesforce, self.entity_name).delete(record_id)


class AccountRepository(ReadWriteRepository):
    """
    Account Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Account data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Account/FieldsAndRelationships/view
    """

    entity_name = 'Account'


class ContactRepository(ReadWriteRepository):
    """
    Contact Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Contacts data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/FieldsAndRelationships/view
    """

    entity_name = 'Contact'


class EventAttendeeRepository(ReadWriteRepository):
    """
    Event Attendee Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Event Attendee data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAX/FieldsAndRelationships/view
    """

    entity_name = 'Event_Attendee__c'


class EventRepository(ReadWriteRepository):
    """
    Event Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Event or Interaction data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I58000001EcAY/FieldsAndRelationships/view
    """

    entity_name = 'Event__c'


class PolicyIssuesRepository(ReadWriteRepository):
    """
    Policy Issues Repository to connect to BED Salesforce API

    Repository pattern for Salesforce interactions with Policy Issues data
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/01I580000011RrH/FieldsAndRelationships/view
    """

    entity_name = 'Policy_Issues__c'
