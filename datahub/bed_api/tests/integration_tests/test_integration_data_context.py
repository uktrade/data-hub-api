import pytest

from datahub.bed_api.data_context import BedDataContext
from datahub.bed_api.entities import Account
from datahub.bed_api.tests.test_utils import NOT_BED_INTEGRATION_TEST_READY


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
    ):
        """
        Test adding and deleting an account

        :param generate_account: New account record generated with faker data
        """
        account_id = None
        with BedDataContext() as bed_data_context:
            try:
                account_id = self.add_and_assert_account(bed_data_context, generate_account)
            finally:
                self.delete_and_assert_account(bed_data_context, account_id)

    def delete_and_assert_account(self, bed_data_context, account_id):
        """
        Delete the account  if there is a value assigned and verify the deletion

        :param bed_data_context: BedDataContext
        :param account_id: Identifier of the new account record
        """
        if account_id:
            bed_data_context.accounts.delete(account_id)
            account_exists = bed_data_context.accounts.exists(account_id)
            assert account_exists is False

    def add_and_assert_account(self, bed_data_context, generate_account):
        """
        Add an account via the bed context or unit of work

        :param bed_data_context: BedDataContext
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
