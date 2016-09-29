"""
These tests rely on the metadata.yaml fixture to be imported,
Check conftest.py in the root folder for the importing mechanism.
"""

import pytest

from django.urls import reverse
from rest_framework import status

# mark the whole module for db use
pytestmark = pytest.mark.django_db


metadata_view_names = (
    'business-type',
    'country',
    'employee-range',
    'interaction-type',
    'sector'
    'role',
    'title',
    'uk-region'

)

metadata_views_ids = (
    'business types view',
    'countries view',
    'employee ranges view',
    'interaction types view',
    'sector view',
    'roles view',
    'titles view',
    'UK regions view'
)


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_get(view_name, api_client):
    """Test a metadata view for 200 only."""
    url = reverse(viewname=view_name)

    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_post(view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=view_name)

    response = api_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_put(view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=view_name)

    response = api_client.put(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize('view_name',
                         metadata_view_names,
                         ids=metadata_views_ids)
def test_metadata_view_patch(view_name, api_client):
    """Test views are read only."""
    url = reverse(viewname=view_name)

    response = api_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


