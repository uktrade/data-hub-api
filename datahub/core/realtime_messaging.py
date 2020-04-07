import logging

from django.conf import settings
from slack import WebClient
from slack.errors import SlackClientError  # the base error class

logger = logging.getLogger(__name__)


def send_realtime_message(message_text):
    """
    Send a message to the realtime messaging system.

    Do not attempt if the messaging config was not set up properly.
    """
    if not (settings.SLACK_API_TOKEN and settings.SLACK_MESSAGE_CHANNEL):
        logger.info('Setup was incomplete. Message not attempted.')
        return

    client = WebClient(
        timeout=settings.SLACK_TIMEOUT_SECONDS,
        token=settings.SLACK_API_TOKEN,
    )
    try:
        client.chat_postMessage(
            channel=settings.SLACK_MESSAGE_CHANNEL,
            text=message_text,
        )
    except SlackClientError:
        logger.error('Slack post failed.', exc_info=True)
