import pytest
from django.urls import reverse
from rest_framework import status

from .factories import AdvisorFactory

pytestmark = pytest.mark.django_db


def test_advisor_list_view(api_client):
    """Should return id and name."""

    advisor = AdvisorFactory(first_name='John', last_name='Smith')
    url = reverse('advisor-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
