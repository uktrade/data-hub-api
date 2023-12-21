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
    """
    Testing to get all fields for client email receipt
    """
    mock_customer_response_instance = MagicMock()
    mock_customer_response_token_instance = MagicMock()
    mock_customer_response_instance.win = mock_win
    mock_customer_response_token_instance.company_contact.email = 'test@example.com'
    mock_customer_response_token_instance.company_contact.first_name = 'John'
    mock_win.country = 'Country'
    mock_win.lead_officer.name = 'Adviser Name'
    mock_win.goods_vs_services = 'Goods and Services'
    with patch('datahub.export_win.models.CustomerResponse.objects.get') as mock_response_get, \
         patch('datahub.export_win.models.CustomerResponseToken.objects.get') as mock_token_get:
        mock_response_get.return_value = mock_customer_response_instance
        mock_token_get.return_value = mock_customer_response_token_instance
        mock_token_id = uuid.uuid4()
        mock_customer_response_token_instance.id = mock_token_id
        result = get_all_fields_for_client_email_receipt(
            mock_customer_response_token_instance, mock_customer_response_instance)
        assert result['customer_email'] == 'test@example.com'
        assert result['country_destination'] == 'Country'
        assert result['client_firstname'] == 'John'
        assert result['lead_officer_name'] == 'Adviser Name'
        assert result['goods_services'] == 'Goods and Services'
        assert result['url'] == f'{settings.EXPORT_WIN_CLIENT_REVIEW_WIN_URL}/{mock_token_id}'


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_for_contact_without_existing_unexpired_token():
    """
    Testing the create token where no existing unexpired token
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    token_exists = CustomerResponseToken.objects.filter(
        id=new_token.id,
        company_contact=mock_contact,
        customer_response=mock_customer_response,
    ).exists()
    assert token_exists is True
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_unexpired_token():
    """
    Testing the creation token where there is existing unexpired token
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    with freeze_time('2023-12-10'):
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),
        )
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    assert new_token.id != existing_token.id
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    existing_token.refresh_from_db()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert existing_token.expires_on <= utc_now


@pytest.mark.django_db
@freeze_time('2023-12-11')
def test_create_token_with_existing_expired_and_unexpired_tokens():
    """
    Testing the creation of a token where there are existing multiple tokens,
    both in expired and unexpired states
    """
    mock_customer_response = CustomerResponseFactory()
    mock_contact = ContactFactory()
    with freeze_time('2023-12-09'):
        expired_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() - timedelta(days=1),
        )
    with freeze_time('2023-12-10'):
        existing_token = CustomerResponseTokenFactory(
            company_contact=mock_contact,
            customer_response=mock_customer_response,
            expires_on=datetime.utcnow() + timedelta(days=1),
        )
    new_token = create_token_for_contact(mock_contact, mock_customer_response)
    assert new_token.id is not None
    assert new_token.id != existing_token.id
    expected_time = datetime.utcnow() + timedelta(days=7)
    assert expected_time == new_token.expires_on
    expired_token.refresh_from_db()
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    assert expired_token.expires_on <= utc_now
    existing_token.refresh_from_db()
    assert existing_token.expires_on <= utc_now
