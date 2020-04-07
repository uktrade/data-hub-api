from unittest import mock

from django.test import override_settings
from slack.errors import SlackClientError  # the base error class

from datahub.core.realtime_messaging import send_realtime_message


class TestRealtimeMessaging():
    """
    Test the realtime messaging wrapper.
    """

    @override_settings(ENABLE_SLACK_MESSAGING=False)
    def test_disabled_facility_aborts_message(self, caplog, monkeypatch):
        """
        Test that an disabling the facility setting aborts the send process gracefully.
        """
        caplog.set_level('INFO')
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        send_realtime_message('some message')
        expected_message = 'Setup was incomplete. Message not attempted.'
        assert expected_message in caplog.text
        mock_web_client().assert_not_called()

    @override_settings(
        SLACK_API_TOKEN=None,
        SLACK_MESSAGE_CHANNEL='MESSAGE_CHANNEL',
    )
    def test_absent_api_token_aborts_message(self, caplog, monkeypatch):
        """
        Test that an absence of Slack API token aborts the send process gracefully.
        """
        caplog.set_level('INFO')
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        send_realtime_message('some message')
        expected_message = 'Setup was incomplete. Message not attempted.'
        assert expected_message in caplog.text
        mock_web_client().assert_not_called()

    @override_settings(
        SLACK_API_TOKEN='API_TOKEN',
        SLACK_MESSAGE_CHANNEL=None,
    )
    def test_absent_message_channel_aborts_message(self, caplog, monkeypatch):
        """
        Test that an absence of a message channel aborts the send process gracefully.
        """
        caplog.set_level('INFO')
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        send_realtime_message('some message')
        expected_message = 'Setup was incomplete. Message not attempted.'
        assert expected_message in caplog.text
        mock_web_client.assert_not_called()

    @override_settings(
        SLACK_API_TOKEN='API_TOKEN',
        SLACK_MESSAGE_CHANNEL='MESSAGE_CHANNEL',
        SLACK_TIMEOUT_SECONDS=11,
    )
    def test_slack_client_initiated(self, monkeypatch):
        """
        Test that the Slack client gets passed the token and timeout from the config.
        """
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        send_realtime_message('some message')
        mock_web_client.assert_called_once_with(
            timeout=11,
            token='API_TOKEN',
        )

    @override_settings(
        SLACK_API_TOKEN='API_TOKEN',
        SLACK_MESSAGE_CHANNEL='MESSAGE_CHANNEL',
    )
    def test_message_method_called(self, monkeypatch):
        """
        Test that the Slack client 'send' method is called appropriately.
        """
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        send_realtime_message('Hello!')
        mock_web_client().chat_postMessage.assert_called_once_with(
            channel='MESSAGE_CHANNEL',
            text='Hello!',
        )

    @override_settings(
        SLACK_API_TOKEN='API_TOKEN',
        SLACK_MESSAGE_CHANNEL='MESSAGE_CHANNEL',
    )
    def test_slack_error_handled(
        self,
        caplog,
        monkeypatch,
    ):
        """
        Test that Slack client errors are caught and reported.
        """
        caplog.set_level('ERROR')
        mock_web_client = mock.Mock()
        monkeypatch.setattr(
            'datahub.core.realtime_messaging.WebClient',
            mock_web_client,
        )
        mock_web_client().chat_postMessage.side_effect = SlackClientError
        send_realtime_message('some message')
        expected_message = 'Slack post failed.'
        assert expected_message in caplog.text
