from simple_salesforce import format_soql

from datahub.bed_api.constants import (
    BusinessArea,
    ContactQuery,
    ContactType,
    JobType,
    Salutation,
)
from datahub.bed_api.factories import BedFactory
from datahub.bed_api.models import EditContact
from datahub.bed_api.repositories import AccountRepository, ContactRepository


class TestContactRepositoryShould:
    """Unit tests for ContactRepository"""
#     TODO


class TestIntegrationContactRepositoryShould:
    """
    Integration Tests needing BED configuration within
    env - see Vault for valid settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_utilise_crud_operations(self):
        """
        Test BedFactory integration with the real configuration values generates
        an actual Salesforce session instance
        """
        contact_repository = self.create_contact_repository()
        # Get test Account to associate contact with
        account_repository = self.create_account_repository()
        test_account = account_repository.get('0010C00000KSGD4QAP')
        assert test_account is not None
        # from pprint import pprint
        # pprint('---------------------------------')
        # Create minimal contact - TODO: Generate with Faker
        contact = EditContact(
            salutation=Salutation.mrs,
            first_name='Jane',
            last_name='Doe',
            email='jane.doe@madetech.com',
            account_id=test_account['Id'],
        )
        contact.MiddleName = 'Middleton'
        contact.Phone = '0797396740'
        contact.MobilePhone = '0797396741'
        contact.Notes__c = 'Integration Test Notes'
        # CHECK: if this should be defaulted internally
        contact.Contact_Type__c = ContactType.external
        contact.Job_Title__c = 'Business Analyst'
        contact.Job_Type__c = JobType.consultant
        contact.Business_Area__c = BusinessArea.professional
        # pprint('New Contact ...')
        # pprint(contact.as_blank_clean_dict())
        # response = contact_repository.upsert(record_id='Id', contact.as_blank_clean_dict())
        response = contact_repository.add(**contact.as_blank_clean_dict())
        assert response is not None
        # pprint(response)
        # pprint('---------------------------------')
        # Query Contact
        actual = contact_repository.query(
            format_soql(ContactQuery.get_by_id.value.sql, id='0030C00000KSbt4QAD'),
        )
        assert actual is not None
        assert actual['totalSize'] == 1
        assert actual['done'] is True
        assert actual['records'][0]['Id'] == '0030C00000KSbt4QAD'

        #  Update Contact

        #  Finally delete Contact

    # Setup as fixtures ...
    def create_salesforce(self):
        """Create salesforce instance"""
        factory = BedFactory()
        salesforce = factory.create()
        return salesforce

    def create_contact_repository(self):
        """Creates instance of contact repository"""
        salesforce = self.create_salesforce()
        repository = ContactRepository(salesforce)
        return repository

    def create_account_repository(self):
        """Creates instance of account repository"""
        salesforce = self.create_salesforce()
        repository = AccountRepository(salesforce)
        return repository
