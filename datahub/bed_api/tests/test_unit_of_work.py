import os
from unittest import mock

import pytest

from datahub.bed_api.models import EditAccount, EditContact
from datahub.bed_api.unit_of_work import BedUnitOfWork
from datahub.core.test_utils import mock_environ


class TestBedUnitOfWorkShould:
    """
    Unit Tests for BED Unit of Work maps all the exposed repositories
    within a single unit of work
    """

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='False',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_sales_force_session_gets_created_and_closed(
            self,
            mock_salesforce,
    ):
        """
        Test BedUnitOfWork is built with Salesforce session
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with BedUnitOfWork() as bed_context:
            assert bed_context is not None
            assert mock_salesforce.called
            assert mock_salesforce.call_args_list == [
                mock.call(
                    username='test-user@digital.trade.gov.uk',
                    password='test-password',
                    security_token='test-token',
                ),
            ]

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='False',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_repositories_created(
            self,
            mock_salesforce,
    ):
        """
         Test BedUnitOfWork is built with Salesforce session
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with BedUnitOfWork() as bed_context:
            assert mock_salesforce.called
            assert bed_context.accounts is not None
            assert bed_context.contacts is not None

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='False',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_session_automatically_closes_the_session(
        self,
        mock_salesforce,
    ):
        """Test BedUnitOfWork closes the session"""
        with BedUnitOfWork() as bed_context:
            assert bed_context is not None
        mock_close = mock_salesforce.return_value.session.close
        assert mock_close.calledonce


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    'BED_SECURITY_TOKEN' not in os.environ,
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
            generate_account: EditAccount,
            generate_contact: EditContact,
    ):
        """
        Test adding and deleting an account
        :param generate_account: New account record generated with faker data
        :param generate_contact: New contact record generated with faker data
        """
        account_id = None
        contact_id = None

        with BedUnitOfWork() as bed_context:
            try:
                account_id = self.add_and_assert_account(bed_context, generate_account)
                generate_contact.AccountId = account_id
                contact_id = self.add_and_assert_contact(bed_context, generate_contact)
            finally:
                self.delete_and_assert_contact(bed_context, contact_id)
                self.delete_and_assert_account(bed_context, account_id)

    def delete_and_assert_account(self, bed_context, account_id):
        """
        Delete the account  if there is a value assigned and verify the deletion
        :param bed_context: BedUnitOfWork
        :param account_id: Identifier of the new account record
        """
        if account_id:
            bed_context.accounts.delete(account_id)
            account_exists = bed_context.accounts.exists(account_id)
            assert account_exists is False

    def delete_and_assert_contact(self, bed_context, contact_id):
        """
        Delete the contact  if there is a value assigned and verify the deletion
        :param bed_context: BedUnitOfWork
        :param contact_id: Identifier of the new contact record
        """
        if contact_id:
            bed_context.contacts.delete(contact_id)
            contact_exists = bed_context.contacts.exists(contact_id)
            assert contact_exists is False

    def add_and_assert_contact(self, bed_context, generate_contact):
        """
        Add a contact and verify it exists
        :param bed_context: BedUnitOfWork
        :param generate_contact: New contact record generated with faker data
        :return: Contact id of new contact
        """
        contact_add_response = bed_context.contacts.add(generate_contact.as_all_values_dict())
        assert contact_add_response is not None
        assert contact_add_response['success'] is True
        contact_id = contact_add_response['id']
        assert contact_id is not None
        return contact_id

    def add_and_assert_account(self, bed_context, generate_account):
        """
        Add an account via the bed context or unit of work
        :param bed_context: BedUnitOfWork
        :param generate_account: New account record generated with faker data
        :return: account id of new Account
        """
        account_add_response = bed_context.accounts.add(
            generate_account.as_values_only_dict(),
        )
        assert account_add_response is not None
        assert account_add_response['success'] is True
        account_id = account_add_response['id']
        assert account_id is not None
        return account_id
