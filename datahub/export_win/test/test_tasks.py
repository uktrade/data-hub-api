import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytz
from django.conf import settings

from freezegun import freeze_time

from datahub.company.test.factories import ContactFactory
from datahub.export_win.models import CustomerResponseToken

from datahub.export_win.tasks import (
    create_token_for_contact,
    get_all_fields_for_client_email_receipt,
)
from datahub.export_win.test.factories import CustomerResponseFactory, CustomerResponseTokenFactory


@pytest.fixture
def mock_customer_response():
    return MagicMock()


@pytest.fixture
def mock_customer_response_token():
    return MagicMock()


@pytest.fixture
def mock_win():
    return MagicMock()


def test_get_all_fields_for_client_email_receipt_success(
    mock_customer_response: MagicMock,
    mock_customer_response_token: MagicMock,
    mock_win: MagicMock,
):
    # Create mocked instances
    mock_customer_response_instance = MagicMock()
    mock_customer_response_token_instance = MagicMock()
    # Set up mock object attributes
    mock_customer_response_instance.win = mock_win
    mock_customer_response_token_instance.company_contact.email = 'test@example.com'
    mock_customer_response_token_instance.company_contact.first_name = 'John'
    mock_win.country = 'Country'
    mock_win.lead_officer.name = 'Adviser Name'
    mock_win.goods_vs_services = 'Goods and Services'
    # Patch the necessary methods with mock objects
    with patch('datahub.export_win.models.CustomerResponse.objects.get') as mock_response_get, \
         patch('datahub.export_win.models.CustomerResponseToken.objects.get') as mock_token_get:
        # Set up return values for the mocked methods
        mock_response_get.return_value = mock_customer_response_instance
        mock_token_get.return_value = mock_customer_response_token_instance
        # Generate a specific ID for the mock token instance
        mock_token_id = uuid.uuid4()
        mock_customer_response_token_instance.id = mock_token_id
        # Call the function under test with mock data objects
        result = get_all_fields_for_client_email_receipt(
            mock_customer_response_token_instance, mock_customer_response_instance)
        # Assertions for the expected values
        assert result['customer_email'] == 'test@example.com'
        assert result['country_destination'] == 'Country'
        assert result['client_firstname'] == 'John'
        assert result['lead_officer_name'] == 'Adviser Name'
        assert result['goods_services'] == 'Goods and Services'
        # Compare the generated URL with the expected URL using the specific ID
        assert result['url'] == f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{mock_token_id}'


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_for_contact_without_existing_unexpired_token():
    # Create instances for CustomerResponse and Contact
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    # Call the function being tested
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    # Check if a token was created for the given contact and customer response
    assert new_token.id is not None  # Assert that the token ID is not None
    token_exists = CustomerResponseToken.objects.filter(
        id=new_token.id,
        company_contact=mock_contact,
        customer_response=mock_customer_response,
    ).exists()
    # Assert that a token was created with new id for the given contact and customer response
    assert token_exists is True
    # Validate the expiry time without formatting
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_unexpired_token():
    # Create instances for CustomerResponse and Contact
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    # Create an existing unexpired token for the contact and customer response
    with freeze_time('2023-12-10'):  # Freeze time for creating the existing token
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),  # Assuming 1 day from now
        )
    # Call the function being tested
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    # Check if a new token was created for the given contact and customer response
    assert new_token.id is not None
    # Assert that a new token was created with a different ID
    assert new_token.id != existing_token.id
    # Validate the expiry time of the new token (7 days from now)
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    # Check if the existing token is set to expire (set to current time)
    existing_token.refresh_from_db()
    # Make datetime.utcnow() timezone-aware
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert existing_token.expires_on <= utc_now


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_expired_and_unexpired_tokens():
    # Create instances for CustomerResponse and Contact
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    # Create an existing expired token for the contact and customer response
    with freeze_time('2023-12-09'):  # Freeze time for creating the expired token
        expired_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() - timedelta(days=1),  # Expired 1 day ago
        )
    # Create an existing unexpired token for the contact and customer response
    with freeze_time('2023-12-10'):  # Freeze time for creating the unexpired token
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),  # Expires 1 day from now
        )
    # Call the function being tested
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    # Check if a new token was created for the given contact and customer response
    assert new_token.id is not None
    # Assert that a new token was created with a different ID than the existing token
    assert new_token.id != existing_token.id
    # Validate the expiry time of the new token (7 days from now)
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    # Check if the existing expired token is still expired
    expired_token.refresh_from_db()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert expired_token.expires_on <= utc_now
    # Check if the existing unexpired token is set to expire (set to current time)
    existing_token.refresh_from_db()
    assert existing_token.expires_on <= utc_now
