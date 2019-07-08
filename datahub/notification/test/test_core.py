import pytest

from datahub.notification import client


@pytest.mark.parametrize(
    'context',
    (
        (None,),
        ({'foo': 'bar'},),
    ),
)
def test_send_email_notification(context):
    """
    Test that NotificationClient.send_email_notification method
    works calls through
    to the underlying notify library as expected.
    """
    client.send_email_notification('john.smith@example.net', 'foobar', context)
    expected_context = context
    if not context:
        expected_context = {}
    notification_api_client = client.client
    notification_api_client.send_email_notification.assert_called_with(
        email_address='john.smith@example.net',
        template_id='foobar',
        personalisation=expected_context,
    )
