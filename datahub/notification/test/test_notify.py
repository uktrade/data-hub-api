import pytest

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.notification import client
from datahub.notification.notify import (
    notify_adviser_by_email,
    notify_contact_by_email,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'adviser_data',
    (
        ({'contact_email': ''}),
        ({}),
    ),
)
def test_notify_adviser_by_email(adviser_data):
    """
    Test the notify_adviser_by_email utility.
    """
    notification_api_client = client.client
    adviser = AdviserFactory(**adviser_data)
    notify_adviser_by_email(adviser, 'foobar', {'abc': '123'})
    notification_api_client.send_email_notification.assert_called_with(
        email_address=adviser.contact_email or adviser.email,
        template_id='foobar',
        personalisation={'abc': '123'},
    )


@pytest.mark.django_db
def test_notify_contact_by_email():
    """
    Test the notify_contact_by_email utility.
    """
    notification_api_client = client.client
    contact = ContactFactory()
    notify_contact_by_email(contact, 'foobar', {'abc': '123'})
    notification_api_client.send_email_notification.assert_called_with(
        email_address=contact.email,
        template_id='foobar',
        personalisation={'abc': '123'},
    )
