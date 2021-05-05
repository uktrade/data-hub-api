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

    # TODO: Refactor into separate tests
    def test_utilise_crud_operations(self):
        """
        Test BedFactory integration with the real configuration values generates
        an actual Salesforce session instance
        """
        contact_repository = self.create_contact_repository()
        account_repository = self.create_account_repository()
        # Made Tech test account
        test_account = account_repository.get('0010C00000KSGD4QAP')
        assert test_account is not None
        # from pprint import pprint
        # pprint('---------------------------------')
        # Create minimal contact - TODO: Generate with Faker
        contact = EditContact(
            salutation=Salutation.mrs,
            first_name='Maya',
            last_name='Doe',
            email='maya.doe@madetech.com',
            account_id=test_account['Id'],
        )
        contact.Suffix = 'Developer'
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
        contact_add_response = contact_repository.add(contact.as_blank_clean_dict())
        assert contact_add_response is not None
        assert contact_add_response['success'] is True
        new_contact_id = contact_add_response['id']
        # print('New Contact Response ...')
        # pprint(contact_add_response)
        actual = contact_repository.query(
            format_soql(ContactQuery.get_by_id.value.sql, id=new_contact_id),
        )
        assert actual is not None
        assert actual['totalSize'] == 1
        assert actual['done'] is True
        assert actual['records'][0]['Id'] == new_contact_id

        #  Update Contact
        contact.Notes__c = 'Integration Test Notes - Update'
        update_contact_response = contact_repository.upsert(
            f'Id/{new_contact_id}', contact.as_blank_clean_dict())
        # print('Update Contact Response ...')
        # pprint(update_contact_response)
        assert update_contact_response is not None
        assert update_contact_response == 204

        #  Finally delete Contact
        delete_contact_response = contact_repository.delete(new_contact_id)
        # pprint(delete_contact_response)
        assert delete_contact_response is not None
        assert delete_contact_response == 204
        # pprint('---------------------------------')

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
