import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from datahub.export_win.tasks import get_all_fields_for_client_email_receipt


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
