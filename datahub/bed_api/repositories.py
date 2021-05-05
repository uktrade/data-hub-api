import abc

from simple_salesforce import Salesforce


class AbstractRepository(abc.ABC):
    """
    Base Abstract Repository Class fashioned more to fit the Salesforce paradigm
    """

    def __init__(self, salesforce: Salesforce):
        """
        Salesforce
        :param salesforce:
        """
        self.salesforce = salesforce

    # @abc.abstractmethod
    def add(self, data):
        """
        Creates a new SObject using a POST
        :param data: A dict of the data to create the SObject from
        :return: Returns NotImplementedError
        """
        raise NotImplementedError

    # @abc.abstractmethod
    def upsert(self, record_id, data):
        """
        Create or Update based on some unique identifier
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Returns NotImplementedError
        """
        raise NotImplementedError

    # @abc.abstractmethod
    def get(self, record_id):
        """
        Get a single item by unique identifier
        :param record_id: Unique identifier value
        :return: NotImplementedError
        """
        raise NotImplementedError

    # @abc.abstractmethod
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
        :param query:
        :param include_deleted:
        :param kwargs:
        :return: Salesforce SOQL query
        """
        return self.salesforce.query(query, include_deleted, **kwargs)

    def query_more(
        self,
        next_records_identifier,
        identifier_is_url=False,
        include_deleted=False,
        **kwargs,
    ):
        """
        Retrieves more results from a query that returned more results
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

    # @abc.abstractmethod
    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Record id for deleting data
        :return: NotImplementedError
        """
        raise NotImplementedError


class ContactRepository(AbstractRepository):
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

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Contact.delete(record_id)

    def get(self, record_id):
        """
        Get single item by identifier
        :param record_id: Unique identifier value
        :return:
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
        return self.salesforce.Contact.get_by_custom_id(custom_id_field, custom_id_value)

    def add(self, data):
        """
        Add a new Contact using a POST
        :param data: A dict of Contact data
        :return: Returns New Contact
        """
        return self.salesforce.Contact.create(data)

    def upsert(self, record_id, data):
        """
        Create or Update Contact
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated
        """
        return self.salesforce.Contact.upsert(record_id, data)


class AccountRepository(AbstractRepository):
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

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Unique identifier for deleting records
        :return: Result of deletion
        """
        return self.salesforce.Account.delete(record_id)

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
        return self.salesforce.Account.get_by_custom_id(custom_id_field, custom_id_value)

    def add(self, data):
        """
        Add a new Account using a POST
        :param data: A dict of Account data
        :return: Returns New Account
        """
        return self.salesforce.Contact.create(data)

    def upsert(self, record_id, data):
        """
        Create or Update Contact
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Created or updated Account
        """
        return self.salesforce.Account.upsert(record_id, data)
