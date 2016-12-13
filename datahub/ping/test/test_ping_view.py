from unittest import mock
from unittest.mock import Mock

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


@mock.patch('datahub.ping.services.KorbenConnector')
def test_all_good(mock_korben_connector, client):
    mock_korben_connector().ping.return_value = Mock(status_code=status.HTTP_200_OK)
    url = reverse('ping')
    response = client.get(url)
    assert '<status>OK</status>' in str(response.content)


@mock.patch('datahub.ping.services.KorbenConnector')
def test_korben_not_returning_200(mock_korben_connector, client):
    korben_error_content = """foobar"""
    mock_korben_connector().ping.return_value = Mock(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=korben_error_content
    )
    url = reverse('ping')
    response = client.get(url)
    assert '<status>False</status>' in str(response.content)


