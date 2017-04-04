
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

pytestmark = pytest.mark.django_db


def test_all_good(client):
    """Test all good."""
    url = reverse('ping')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert '<status>OK</status>' in str(response.content)
    assert response._headers['content-type'] == ('Content-Type', 'text/xml')
