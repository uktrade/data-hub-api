
from unittest.mock import patch

import pytest
from django.db import DatabaseError

from rest_framework import status
from rest_framework.reverse import reverse

pytestmark = pytest.mark.django_db


def test_all_good(client):
    """Test all good."""
    url = reverse('ping')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert '<status>OK</status>' in str(response.content)
    assert response.headers['content-type'] == 'text/xml'


def test_check_database_fail(client):
    url = reverse('ping')
    with patch(
        'datahub.ping.services.Company.objects.all',
        side_effect=DatabaseError('No database'),
    ):
        response = client.get(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert '<status>FALSE</status>' in str(response.content)
        assert response.headers['content-type'] == 'text/xml'
