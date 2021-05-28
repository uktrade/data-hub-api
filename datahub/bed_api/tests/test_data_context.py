from unittest import mock

from datahub.bed_api.data_context import BedDataContext
from datahub.core.test_utils import mock_environ


class TestBedDataContextShould:
    """
    Unit Tests for BED Unit of Work maps all the exposed repositories
    within a single unit of work
    """

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='false',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_salesforce_session_gets_created_and_closed(
        self,
        mock_salesforce,
    ):
        """
        Test BedDataContext is built with Salesforce session
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with BedDataContext() as bed_data_context:
            assert bed_data_context is not None
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
        BED_IS_SANDBOX='false',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_repositories_created(
        self,
        mock_salesforce,
    ):
        """
         Test BedDataContext is built with Salesforce session
        :param mock_salesforce: Monkeypatch for Salesforce
        """
        with BedDataContext() as bed_data_context:
            assert mock_salesforce.called
            assert bed_data_context.accounts is not None
            assert bed_data_context.contacts is not None

    @mock_environ(
        BED_USERNAME='test-user@digital.trade.gov.uk',
        BED_PASSWORD='test-password',
        BED_SECURITY_TOKEN='test-token',
        BED_IS_SANDBOX='false',
    )
    @mock.patch('datahub.bed_api.factories.Salesforce')
    def test_session_automatically_closes_the_session(
        self,
        mock_salesforce,
    ):
        """Test BedDataContext closes the session"""
        with BedDataContext() as bed_data_context:
            assert bed_data_context is not None
        mock_close = mock_salesforce.return_value.session.close
        assert mock_close.calledonce
