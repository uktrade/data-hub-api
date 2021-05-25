import pytest

from datahub.bed_api.entities import Account, Contact
from datahub.bed_api.tests.test_utils import NOT_BED_INTEGRATION_TEST_READY
from datahub.bed_api.unit_of_work import BedUnitOfWork


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationBedUnitOfWorkShould:
    """
    Integration Test for
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_creation_and_deletion_of_an_account(
        self,
        generate_account: Account,
        generate_contact: Contact,
    ):
        """
        Test adding and deleting an account
        :param generate_account: New account record generated with faker data
        :param generate_contact: New contact record generated with faker data
        """
        account_id = None
        contact_id = None
        with BedUnitOfWork() as bed_data_context:
            try:
                account_id = self.add_and_assert_account(bed_data_context, generate_account)
                generate_contact.AccountId = account_id
                contact_id = self.add_and_assert_contact(bed_data_context, generate_contact)
            finally:
                self.delete_and_assert_contact(bed_data_context, contact_id)
                self.delete_and_assert_account(bed_data_context, account_id)

    def delete_and_assert_account(self, bed_data_context, account_id):
        """
        Delete the account  if there is a value assigned and verify the deletion
        :param bed_data_context: BedUnitOfWork
        :param account_id: Identifier of the new account record
        """
        if account_id:
            bed_data_context.accounts.delete(account_id)
            account_exists = bed_data_context.accounts.exists(account_id)
            assert account_exists is False

    def delete_and_assert_contact(self, bed_data_context, contact_id):
        """
        Delete the contact  if there is a value assigned and verify the deletion
        :param bed_data_context: BedUnitOfWork
        :param contact_id: Identifier of the new contact record
        """
        if contact_id:
            bed_data_context.contacts.delete(contact_id)
            contact_exists = bed_data_context.contacts.exists(contact_id)
            assert contact_exists is False

    def add_and_assert_contact(self, bed_data_context, generate_contact):
        """
        Add a contact and verify it exists
        :param bed_data_context: BedUnitOfWork or db context with salesforce
        :param generate_contact: New contact record generated with faker data
        :return: Contact id of new contact
        """
        contact_add_response = bed_data_context.contacts.add(
            generate_contact.as_all_values_dict(),
        )
        assert contact_add_response is not None
        assert contact_add_response['success'] is True
        contact_id = contact_add_response['id']
        assert contact_id is not None
        return contact_id

    def add_and_assert_account(self, bed_data_context, generate_account):
        """
        Add an account via the bed context or unit of work
        :param bed_data_context: BedUnitOfWork
        :param generate_account: New account record generated with faker data
        :return: account id of new Account
        """
        account_add_response = bed_data_context.accounts.add(
            generate_account.as_values_only_dict(),
        )
        assert account_add_response is not None
        assert account_add_response['success'] is True
        account_id = account_add_response['id']
        assert account_id is not None
        return account_id
