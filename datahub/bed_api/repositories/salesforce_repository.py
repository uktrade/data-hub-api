from simple_salesforce import Salesforce


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
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Record id for deleting data
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def exists(self, record_id):
        """
        Checks if the record exists using the most unique identifier and
        the most efficient mechanism for checking ie the least content
        with ideally a head verb
        :param record_id: Unique identifier value, associated with Id value typically
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def get(self, record_id):
        """
        Get a single item by unique identifier
        :param record_id: Unique identifier value
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def get_by(self, custom_id_field, custom_id_value):
        """
        Returns the result of a GET by field
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id_value: External ID value
        :raises: NotImplementedError
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
        :raises: NotImplementedError
        """
        raise NotImplementedError

    def exists_status(self, record_id, response) -> bool:
        """
        Check if a record exists by the response
        :param record_id: Unique identifier
        :param response: Response returned from query by id
        :return: True if response assigned, totalSize is
                 greater than 1 and there is a record id
                 the equivalent of that value
        """
        return (
            response is not None
            and response['totalSize'] >= 1
            and len(response['records']) > 0
            and response['records'][0].get('Id') == record_id
        )
