import pytest
from django.urls import reverse

from .factories import AdvisorFactory

pytestmark = pytest.mark.django_db


def test_advisor_list_view(api_client):
    """Should return id and name."""

    advisor = AdvisorFactory(first_name='John', last_name='Smith')
    url = reverse('advisor-list')
    response = api_client.get(url)

    assert response.data['results'][0]['name'] == advisor.name
    assert response.data['results'][0]['id'] == str(advisor.id)

