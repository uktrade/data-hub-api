from simple_salesforce import format_soql, Salesforce

from datahub.bed_api.constants import AccountQuery, ContactQuery


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
        :return: Returns NotImplementedError
        """
        raise NotImplementedError

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Record id for deleting data
        :return: NotImplementedError
        """
        raise NotImplementedError

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier and
        the most efficient mechanism for checking ie the least content
        with ideally a head verb
        :param record_id: Unique identifier value, associated with Id value typically
        :return: NotImplementedError
        """
        raise NotImplementedError

    def get(self, record_id):
        """
        Get a single item by unique identifier
        :param record_id: Unique identifier value
        :return: NotImplementedError
        """
        raise NotImplementedError

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :return: NotImplementedError
        """
        raise NotImplementedError

    def query(self, query, include_deleted=False, **kwargs):
        """
        Return the result of a Salesforce SOQL query as a dict decoded from
        the Salesforce response JSON payload.
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
        response JSON payload
        """
        return self.salesforce.query_more(
            next_records_identifier,
            identifier_is_url,
            include_deleted,
            **kwargs,
        )

    def upsert(self, record_id, data):
        """
        Create or Update based on some unique identifier
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Returns NotImplementedError
        """
        raise NotImplementedError


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
        return (
            response is not None
            and response['totalSize'] >= 1
            and response['done'] is True
            and response['records'][0]['Id'] == record_id
        )

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
            custom_id_field, custom_id_value
        )

    def upsert(self, record_id, data):
        """
        Create or Update Contact
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated
        """
        return self.salesforce.Contact.upsert(record_id, data)


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
        return (
            response is not None
            and response['totalSize'] >= 1
            and response['done'] is True
            and response['records'][0]['Id'] == record_id
        )

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
        :return: Contact record or None
        """
        return self.salesforce.Account.get_by_custom_id(
            custom_id_field,
            custom_id_value,
        )

    def upsert(self, record_id, data):
        """
        Create or Update Contact
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated Account
        """
        return self.salesforce.Account.upsert(record_id, data)
