import pytest

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.notification import notify_gateway
from datahub.notification.constants import DEFAULT_SERVICE_NAME, OMIS_SERVICE_NAME
from datahub.notification.notify import (
    notify_adviser_by_email,
    notify_by_email,
    notify_contact_by_email,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'adviser_data,notify_service_name',
    (
        ({'contact_email': ''}, None),
        ({}, OMIS_SERVICE_NAME),
    ),
)
def test_notify_adviser_by_email(adviser_data, notify_service_name):
    """
    Test the notify_adviser_by_email utility.
    """
    expected_notify_service_name = notify_service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_notify_service_name]
    adviser = AdviserFactory(**adviser_data)
    notify_adviser_by_email(adviser, 'foobar', {'abc': '123'}, notify_service_name)
    notification_api_client.send_email_notification.assert_called_with(
        email_address=adviser.contact_email or adviser.email,
        template_id='foobar',
        personalisation={'abc': '123'},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'notify_service_name',
    (
        None,
        OMIS_SERVICE_NAME,
    ),
)
def test_notify_contact_by_email(notify_service_name):
    """
    Test the notify_contact_by_email utility.
    """
    expected_notify_service_name = notify_service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_notify_service_name]
    contact = ContactFactory()
    notify_contact_by_email(contact, 'foobar', {'abc': '123'}, notify_service_name)
    notification_api_client.send_email_notification.assert_called_with(
        email_address=contact.email,
        template_id='foobar',
        personalisation={'abc': '123'},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'notify_service_name',
    (
        None,
        OMIS_SERVICE_NAME,
    ),
)
def test_notify_by_email(notify_service_name):
    """
    Test the notify_by_email utility.
    """
    expected_notify_service_name = notify_service_name or DEFAULT_SERVICE_NAME
    notification_api_client = notify_gateway.clients[expected_notify_service_name]
    email_address = 'foo@example.net'
    notify_by_email(email_address, 'foobar', {'abc': '123'}, notify_service_name)
    notification_api_client.send_email_notification.assert_called_with(
        email_address=email_address,
        template_id='foobar',
        personalisation={'abc': '123'},
    )
