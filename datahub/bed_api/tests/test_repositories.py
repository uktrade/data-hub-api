from unittest import mock

import pytest
from simple_salesforce import format_soql

from datahub.bed_api.constants import ContactQuery
from datahub.bed_api.models import EditAccount, EditContact
from datahub.bed_api.repositories import (
    AccountRepository,
    ContactRepository,
    SalesforceRepository,
)
from datahub.bed_api.tests.test_utils import (
    create_fail_query_response,
    create_success_query_response,
    NOT_BED_INTEGRATION_TEST_READY,
)


class TestSalesforceRepositoryShould:
    """Unit tests for Base SalesforceRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_query_calls_salesforce_query_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test query_more calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = SalesforceRepository(mock_salesforce)
        expected_query = 'test_query'
        expected_included_delete = True

        repository.query(
            expected_query,
            expected_included_delete,
            test=True,
        )

        assert mock_salesforce.query.called
        assert mock_salesforce.query.call_args == mock.call(
            expected_query,
            expected_included_delete,
            test=True,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_query_next_calls_salesforce_query_more_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test query_more calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = SalesforceRepository(mock_salesforce)
        expected_next_records_identifier = 'test_next_id'
        expected_identifier_is_url = True
        expected_included_delete = True

        repository.query_next(
            expected_next_records_identifier,
            expected_identifier_is_url,
            expected_included_delete,
            test=True,
        )

        assert mock_salesforce.query_more.called
        assert mock_salesforce.query_more.call_args == mock.call(
            expected_next_records_identifier,
            expected_identifier_is_url,
            expected_included_delete,
            test=True,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test add throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.add({'TestData': True})

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test delete throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.delete('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test exists throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.exists('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test exists throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.get('test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test get_by throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.get_by('test_field', 'test_record_id')

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_upsert_throws_not_implemented_error_by_default(
        self,
        mock_salesforce,
    ):
        """
        Test upsert throws NotImplementedError
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with pytest.raises(NotImplementedError):
            repository = SalesforceRepository(mock_salesforce)

            repository.upsert('test_record_id', {'TestData': True})


class TestContactRepositoryShould:
    """Unit tests for ContactRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_contact_add_with_valid_args(
        self,
        mock_salesforce,
        generate_contact: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_contact: Generated contact data
        """
        repository = ContactRepository(mock_salesforce)

        repository.add(generate_contact.as_values_only_dict())

        assert mock_salesforce.Contact.create.called
        assert mock_salesforce.Contact.create.call_args == mock.call(
            generate_contact.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_contact_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Contact.delete.called
        assert mock_salesforce.Contact.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Contact',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.ContactRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.ContactRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_contact_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Contact.get.called
        assert mock_salesforce.Contact.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_contact_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Contact.get_by_custom_id.called
        assert mock_salesforce.Contact.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_upsert_calls_salesforce_contact_upsert_with_valid_args(
        self,
        mock_salesforce,
        generate_contact: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_contact: Generated contact data
        """
        repository = ContactRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_contact.Id = expected_record_id

        repository.upsert(expected_record_id, generate_contact.as_values_only_dict())

        assert mock_salesforce.Contact.upsert.called
        assert mock_salesforce.Contact.upsert.call_args == mock.call(
            'test_record_id',
            generate_contact.as_values_only_dict(),
        )


class TestAccountRepositoryShould:
    """Unit tests for AccountRepository"""

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_add_calls_salesforce_contact_add_with_valid_args(
        self,
        mock_salesforce,
        generate_account: EditAccount,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_account: Generated account data
        """
        repository = AccountRepository(mock_salesforce)

        repository.add(generate_account.as_values_only_dict())

        assert mock_salesforce.Account.create.called
        assert mock_salesforce.Account.create.call_args == mock.call(
            generate_account.as_values_only_dict(),
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_delete_calls_salesforce_account_delete_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test delete calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.delete(expected_record_id)

        assert mock_salesforce.Account.delete.called
        assert mock_salesforce.Account.delete.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_true_when_query_response_succeeds(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        success_query_response = create_success_query_response(
            'Account',
            expected_record_id,
        )

        with mock.patch(
            'datahub.bed_api.repositories.AccountRepository.query',
            return_value=success_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is True

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_exists_return_false_when_query_response_fails(
        self,
        mock_salesforce,
    ):
        """
        Test exists calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        failed_query_response = create_fail_query_response()

        with mock.patch(
            'datahub.bed_api.repositories.AccountRepository.query',
            return_value=failed_query_response,
        ):
            exists_response = repository.exists(expected_record_id)

            assert exists_response is False

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_calls_salesforce_account_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'

        repository.get(expected_record_id)

        assert mock_salesforce.Account.get.called
        assert mock_salesforce.Account.get.call_args == mock.call(
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_get_by_calls_salesforce_account_get_with_valid_args(
        self,
        mock_salesforce,
    ):
        """
        Test get_by calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_field = 'test_record_field'
        expected_record_id = 'test_record_id'

        repository.get_by(expected_record_field, expected_record_id)

        assert mock_salesforce.Account.get_by_custom_id.called
        assert mock_salesforce.Account.get_by_custom_id.call_args == mock.call(
            expected_record_field,
            expected_record_id,
        )

    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_upsert_calls_salesforce_account_upsert_with_valid_args(
        self,
        mock_salesforce,
        generate_account: EditContact,
    ):
        """
        Test add calls Salesforce with the correct Arguments
        :param mock_salesforce: Monkeypatch for Salesforce
        :param generate_account: Generated account data
        """
        repository = AccountRepository(mock_salesforce)
        expected_record_id = 'test_record_id'
        generate_account.Id = expected_record_id

        repository.upsert(expected_record_id, generate_account.as_values_only_dict())

        assert mock_salesforce.Account.upsert.called
        assert mock_salesforce.Account.upsert.call_args == mock.call(
            'test_record_id',
            generate_account.as_values_only_dict(),
        )


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationContactWithAccountRepositoryShould:
    """
    Integration Test Contact and Account Repositories as Contact is dependent on an Account
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_create_an_account_with_contact_utilising(
        self,
        contact_repository,
        account_repository,
        faker,
        generate_account: EditAccount,
        generate_contact: EditContact,
    ):
        """
        Test BedFactory integration with the contact and account repositories
        sampling all functions in an idempotent way, generating potential test
        data for unit tests
        :param contact_repository: ContactRepository fixture
        :param account_repository: AccountRepository fixture
        :param faker: Faker library for generating data
        :param generate_account: New account record generated with faker data
        :param generate_contact: New contact record generated with faker data
        """
        new_contact_id = None
        new_account_id = None
        try:
            # Create a new account / organization / company
            new_account_id = self.generate_and_assert_account(
                account_repository,
                generate_account,
            )

            # Create contact
            generate_contact.AccountId = new_account_id
            new_contact_id = self.generate_and_assert_contact(
                contact_repository,
                generate_contact,
            )
            #  Update Contact
            self.update_and_assert_contact(contact_repository, new_contact_id, faker)

            # TODO Update Account
        finally:
            #  Clean up generated data
            if new_contact_id:
                self.delete_and_assert_contact_deletion(
                    contact_repository,
                    new_contact_id,
                )
            if new_account_id:
                self.delete_and_assert_account_deletion(
                    account_repository,
                    new_account_id,
                )

    def delete_and_assert_account_deletion(
        self,
        account_repository,
        account_id,
    ):
        """
        Delete generated account from the database
        :param account_repository: AccountRepository fixture
        :param account_id: Account id to delete
        """
        delete_account_response = account_repository.delete(account_id)
        assert delete_account_response is not None
        assert delete_account_response == 204
        exists = account_repository.exists(account_id)
        assert exists is False

    def delete_and_assert_contact_deletion(
        self,
        contact_repository,
        contact_id,
    ):
        """
        Delete generated contact from the database
        :param contact_repository: ContactRepository fixture
        :param contact_id: Contact id to delete
        """
        delete_contact_response = contact_repository.delete(contact_id)
        assert delete_contact_response is not None
        assert delete_contact_response == 204
        exists = contact_repository.exists(contact_id)
        assert exists is False

    def update_and_assert_contact(
        self,
        contact_repository,
        new_contact_id,
        faker,
    ):
        """
        Update the contact with basic notes testing update
        :param contact_repository: ContactRepository fixture
        :param new_contact_id: Contact id to update
        :param faker: Faker library
        """
        # Example using original edit object sending all values
        # contact.Notes__c = 'Integration Test Notes - Update'
        # update_contact_response = contact_repository.upsert(
        #     f'Id/{new_contact_id}', contact.as_values_only_dict())
        notes_update = faker.text(max_nb_chars=100)
        update_contact_response = contact_repository.upsert(
            f'Id/{new_contact_id}',
            dict(Notes__c=notes_update),
        )
        assert update_contact_response is not None
        assert update_contact_response == 204

        contact_check = contact_repository.query(
            format_soql(
                ContactQuery.get_notes_by_id.value.sql,
                id=new_contact_id,
            ),
        )
        assert contact_check is not None
        assert contact_check['totalSize'] == 1
        assert contact_check['done'] is True
        assert contact_check['records'][0]['Id'] == new_contact_id
        assert contact_check['records'][0]['Notes__c'] == notes_update

    def generate_and_assert_contact(
        self,
        contact_repository,
        contact: EditContact,
    ):
        """
        Create Account data on Salesforce testing as many ContactRepository
        Methods as possible
        :param contact_repository: ContactRepository fixture
        :param contact: Random Generated Contact
        :return: new contact id
        """
        contact_add_response = contact_repository.add(contact.as_values_only_dict())
        assert contact_add_response is not None
        assert contact_add_response['success'] is True
        contact_id = contact_add_response['id']

        contact_exists = contact_repository.exists(contact_id)
        assert contact_exists is True
        # TODO: Verify all the data has been saved
        return contact_id

    def generate_and_assert_account(
        self,
        account_repository,
        account: EditAccount,
    ):
        """
        Create Account Data on Salesforce using dynamic data
        :param account_repository: AccountRepository fixture
        :param account: New account record generated with faker data
        :return: Account Id
        """
        account_add_response = account_repository.add(account.as_values_only_dict())
        assert account_add_response is not None
        assert account_add_response['success'] is True
        account_id = account_add_response['id']
        assert account_id is not None

        account_exists = account_repository.exists(account_id)
        assert account_exists is True
        # TODO: Assert and verify all data created is correct
        # account_data = account_repository.get(new_account_id)
        return account_id
