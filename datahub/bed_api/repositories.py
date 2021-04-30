import abc

from simple_salesforce import Salesforce


class AbstractRepository(abc.ABC):
    """
    Base Abstract Repository Class fashioned more to fit the Salesforce paradigm
    """

    @abc.abstractmethod
    def upsert(self, record_id, **data):
        """
        Create or Update based on some unique identifier
        :param record_id: Record identifier
        :param data: Represents a dictionary of name values:
        :return: Returns NotImplementedError
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, record_id):
        """
        Get a single item by unique identifier
        :param record_id: Unique identifier value
        :return: NotImplementedError
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_by(self, custom_id_field, custom_id):
        """
        Returns the result of a GET to
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id: External ID value
        :return: NotImplementedError
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, record_id):
        """
        Delete a single item by unique identifier
        :param record_id: Record id for deleting data
        :return: NotImplementedError
        """
        raise NotImplementedError


class ContactRepository(AbstractRepository):
    """
    Contact Repository Pattern for more information on fields see
    https://loginhub--november.lightning.force.com/lightning/setup/ObjectManager/Contact/FieldsAndRelationships/view
    """

    def __init__(self, salesforce: Salesforce):
        """
        Contact Repository
        :param salesforce: Simple Salesforce representing session information
        """
        self.salesforce = salesforce

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

    def get_by(self, custom_id_field, custom_id):
        """
        Custom get not implemented
        :param custom_id_field: API name of a custom field that was defined
                             as an External ID
        :param custom_id: External ID value
        :return: NotImplementedError
        """
        super().get_by(custom_id_field, custom_id)

    def upsert(self, record_id, **data):
        """
        Create or Update Contact
        :param record_id:
        :param data:
        :return:
        """
        return self.salesforce.Contact.upsert(record_id, data)
