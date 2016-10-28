import pytest

from django.urls import reverse
from rest_framework import status

# mark the whole module for db use
from core.test_utils import LeelooTestCase

pytestmark = pytest.mark.django_db


metadata_view_names = (
    'business-type',
    'country',
    'employee-range',
    'interaction-type',
    'sector',
    'service',
    'role',
    'title',
    'turnover',
    'uk-region'
)

metadata_views_ids = (
    'business types view',
    'countries view',
    'employee ranges view',
    'interaction types view',
    'sector view',
    'service view',
    'roles view',
    'titles view',
    'turnover view',
    'UK regions view'
)


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_get(view_name):
    """Test a metadata view for 200 only."""
    url = reverse(viewname=view_name)
    authenticated_api_client = LeelooTestCase().get_logged_in_api_client()
    response = authenticated_api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_post(view_name):
    """Test views are read only."""
    url = reverse(viewname=view_name)
    authenticated_api_client = LeelooTestCase().get_logged_in_api_client()
    response = authenticated_api_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_put(view_name):
    """Test views are read only."""
    url = reverse(viewname=view_name)
    authenticated_api_client = LeelooTestCase().get_logged_in_api_client()
    response = authenticated_api_client.put(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_patch(view_name):
    """Test views are read only."""
    url = reverse(viewname=view_name)
    authenticated_api_client = LeelooTestCase().get_logged_in_api_client()
    response = authenticated_api_client.patch(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
