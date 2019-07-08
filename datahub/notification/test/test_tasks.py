import pytest

from datahub.notification import client
from datahub.notification.tasks import send_email_notification


@pytest.mark.django_db
def test_send_email_notification():
    """
    Test the send_email_notification utility.
    """
    notification_api_client = client.client
    notification_api_client.send_email_notification.return_value = {'id': 'someid'}
    notification_id = send_email_notification('foobar@example.net', 'abcdefg')
    assert notification_id == 'someid'
    notification_api_client.send_email_notification.assert_called_with(
        email_address='foobar@example.net',
        template_id='abcdefg',
        personalisation={},
    )
