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
        BED_TOKEN='test-token',
        BED_IS_SANDBOX='true',
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
        BED_TOKEN='test-token',
        BED_IS_SANDBOX='false',
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
