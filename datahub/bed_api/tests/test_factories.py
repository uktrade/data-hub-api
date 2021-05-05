from unittest import mock

from datahub.bed_api.factories import BedFactory
from datahub.core.test_utils import mock_environ


class TestBedFactory:
    """
    Test BedFactory for creating BED Salesforce instances or sessions
    """

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='True',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_salesforce_instance_generates_sandbox(self, mock_salesforce):
        """
        Test BedFactory creates an instance with the sandbox set to true
        """
        factory = BedFactory()

        factory.create()

        assert mock_salesforce.called
        assert mock_salesforce.call_args_list == [
            mock.call(
                username='test-user@digital.trade.gov.uk',
                password='test-password',
                security_token='test-token',
                domain='test',
            ),
        ]

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='False',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_salesforce_instance_without_sandbox(self, mock_salesforce):
        """
        Test BedFactory creates an instance with the sandbox set to false
        """
        factory = BedFactory()

        factory.create()

        assert mock_salesforce.called
        assert mock_salesforce.call_args_list == [
            mock.call(
                username='test-user@digital.trade.gov.uk',
                password='test-password',
                security_token='test-token',
            ),
        ]


class TestIntegrationBedFactory:
    """
    Integration Tests needing BED configuration within
    env - see Vault for valid settings
        BED_USERNAME
        BED_PASSWORD
        BED_SECURITY_TOKEN
        BED_IS_SANDBOX
    """

    def test_salesforce_generates_sales_force_instance_for_getting_contact_data(self):
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
