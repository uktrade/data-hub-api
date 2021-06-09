import pytest

from datahub.bed_api.entities import (
    Account,
)
from datahub.bed_api.tests.test_utils import (
    assert_all_data_exists_on_bed,
    delete_and_assert_deletion,
    NOT_BED_INTEGRATION_TEST_READY,
)


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationAccountRepositoryShould:
    """
    Integration Test Account Repositories
    NOTE: Integration Tests needing BED configuration within
    .env - see Vault for valid sandbox only settings
         BED_USERNAME
         BED_PASSWORD
         BED_TOKEN
         BED_IS_SANDBOX
    """

    def test_fuzz_on_account_repository(
        self,
        account_repository,
        faker,
        account: Account,
    ):
        """
        Test account repository for basic crud operations

        :param account_repository: AccountRepository fixture
        :param faker: Faker library for generating data
        :param generate_account: New account record generated with faker data
        """
        new_account_id = None
        try:
            # ADD new account / organization / company
            new_account_id = add_and_assert_account(
                account_repository=account_repository,
                account=account,
            )

            #  UPDATE Account
            update_and_assert_account(
                account_repository=account_repository,
                account_id=new_account_id,
                faker=faker,
            )

            # Get by Datahub Id
            get_response = account_repository.get_by_datahub_id(account.datahub_id)
            assert get_response is not None
            assert get_response['Id'] == new_account_id
        finally:
            #  Clean up generated data
            delete_and_assert_deletion(
                repository=account_repository,
                record_id=new_account_id,
            )


def add_and_assert_account(
    account_repository,
    account: Account,
):
    """
    Create Account Data on Salesforce using dynamic data

    :param account_repository: AccountRepository fixture
    :param account: New account record generated with faker data

    :return: New account id
    """
    account_add_response = account_repository.add(
        account.as_values_only_dict(),
    )
    assert account_add_response is not None
    assert account_add_response['success'] is True
    account_id = account_add_response['id']
    assert account_id is not None
    account.id = account_id
    assert_all_data_exists_on_bed(
        bed_entity=account,
        record_id=account_id,
        repository=account_repository,
    )
    return account_id


def update_and_assert_account(
    account_repository,
    account_id,
    faker,
):
    """
    Update the account with basic notes testing update

    :param account_repository: ContactRepository fixture
    :param account_id: Contact id to update
    :param faker: Faker library
    """
    expected_name = faker.company()
    update_contact_response = account_repository.update(
        account_id,
        dict(Name=expected_name),
    )
    assert update_contact_response is not None
    assert update_contact_response == 204

    account_update_check = account_repository.get(account_id)
    assert account_update_check is not None
    assert account_update_check['Name'] == expected_name
