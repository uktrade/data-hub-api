from logging import getLogger

import mailparser
import requests
from django.conf import settings
from django.utils.timezone import now
from rest_framework import status

from datahub.email_ingestion.models import MailboxLogging, MailboxProcessingStatus
from datahub.interaction.email_processors.processors import InteractionPlainEmailProcessor

logger = getLogger(__name__)

BUCKET_ID = 'mailbox'


def _get_headers(token):
    return {
        'Authorization': f'Bearer {token}',
    }


def _get_base_url():
    user_email = settings.MAILBOX_INGESTION_EMAIL
    return f'{settings.MAILBOX_INGESTION_GRAPH_URL}users/{user_email}'


def get_access_token(tenant_id, client_id, client_secret):
    token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default',
    }
    token_request = requests.post(token_url, data=token_data)
    return token_request.json().get('access_token')


def read_messages(token):
    base_url = _get_base_url()
    messages_url = f'{base_url}/mailFolders/Inbox/messages'

    messages_request = requests.get(
        messages_url,
        headers=_get_headers(token),
    )
    messages = messages_request.json().get('value', [])
    return messages


def fetch_message(token, message_id):
    base_url = _get_base_url()
    content_url = f'{base_url}/messages/{message_id}/$value'

    content_request = requests.get(content_url, headers=_get_headers(token))
    if content_request.status_code == status.HTTP_200_OK:
        content = content_request.text
        return content

    return None


def delete_message(token, message_id):
    base_url = _get_base_url()
    delete_path = '/mailFolders/Inbox/messages/'
    delete_url = f'{base_url}{delete_path}{message_id}'

    delete_request = requests.delete(delete_url, headers=_get_headers(token))
    return delete_request.status_code == status.HTTP_204_NO_CONTENT


def process_ingestion_emails():
    """Gets all new mail documents in the bucket and process each message.
    """
    processor = InteractionPlainEmailProcessor()

    token = get_access_token(
        settings.MAILBOX_INGESTION_TENANT_ID,
        settings.MAILBOX_INGESTION_CLIENT_ID,
        settings.MAILBOX_INGESTION_CLIENT_SECRET,
    )

    for message in read_messages(token):
        message_id = message['id']

        content = fetch_message(token, message_id)
        if not content:
            logger.error('Error fetching message: "%s"', message_id)
            continue
        if not delete_message(token, message_id):
            logger.error('Error deleting message: "%s"', message_id)
            continue

        try:
            log = _create_log_entry(message_id, message, content)

            email = mailparser.parse_from_string(content)
            processed, reason, interaction_id = processor.process_email(message=email)
            if not processed:
                _update_log_status(log, MailboxProcessingStatus.FAILURE, reason, None)
                logger.error('Error parsing message: "%s", error: "%s"', message_id, reason)
            else:
                _update_log_status(log, MailboxProcessingStatus.PROCESSED, reason, interaction_id)
                logger.info(reason)
        except Exception as e:
            _update_log_status(log, MailboxProcessingStatus.FAILURE, repr(e), None)
            logger.exception('Error processing message: "%s", error: "%s"', message_id, e)

        logger.info(
            'Successfully processed message "%s" and deleted it from mailbox.',
            message_id,
        )


def _create_log_entry(source, message, content):
    log = MailboxLogging(
        retrieved_on=now(),
        content=content,
        source=source,
        status=MailboxProcessingStatus.RETRIEVED,
    )
    log.save()

    return log


def _update_log_status(log, status, reason, interaction_id):
    log.status = status
    log.extra = reason
    log.interaction_id = interaction_id
    log.save()
