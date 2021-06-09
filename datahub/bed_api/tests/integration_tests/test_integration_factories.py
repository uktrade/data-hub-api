import pytest

from datahub.bed_api.factories import BedFactory
from datahub.bed_api.tests.test_utils import NOT_BED_INTEGRATION_TEST_READY


@pytest.mark.salesforce_test
@pytest.mark.skipif(
    NOT_BED_INTEGRATION_TEST_READY,
    reason='BED security configuration missing from env file',
)
class TestIntegrationBedFactory:
    """
    Integration Tests needing BED configuration within
    env - see Vault for valid settings
        BED_USERNAME
        BED_PASSWORD
        BED_TOKEN
        BED_IS_SANDBOX
    """

    def test_salesforce_generates_salesforce_instance_for_getting_contact_data(self):
        """
        Test BedFactory integration with the real configuration values generates
        an actual Salesforce session instance
        """
        factory = BedFactory()

        actual = factory.create()

        assert actual is not None
        contact_query = actual.Contact.describe()
        assert contact_query is not None
        assert len(contact_query) > 1
