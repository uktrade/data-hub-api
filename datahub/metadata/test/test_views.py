
import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from .. import urls

# mark the whole module for db use

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
    'uk-region',
    'team-role',
    'team',
    'service-delivery-status',
    'event',
    'headquarter-type',
    'company-classification',
    'investment-type',
    'fdi-type',
    'non-fdi-type',
    'referral-source-activity',
    'referral-source-website',
    'referral-source-marketing',
    'investment-business-activity',
    'investment-strategic-driver',
    'salary-range',
    'investment-project-stage',
    'fdi-value',
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
    'UK regions view',
    'teams role view',
    'teams view',
    'service delivery status view',
    'event view',
    'headquarter type view',
    'company classification view',
    'investment type view',
    'fdi type view',
    'non fdi type view',
    'referral source activity view',
    'referral source website view',
    'referral source marketing view',
    'investment business activity view',
    'investment strategic driver view',
    'salary range view',
    'investment project stage view',
    'fdi value view',
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


def test_view_name_generation():
    """Test urls are generated correctly."""
    patterns = urls.urlpatterns
    assert set(pattern.name for pattern in patterns) == set(metadata_view_names)


ordered_metadata_view_params = (
    ('turnover', [
        '£0 to £1.34M',
        '£1.34 to £6.7M',
        '£6.7 to £33.5M',
        '£33.5M+',
    ]),
    ('employee-range', [
        '1 to 9',
        '10 to 49',
        '50 to 249',
        '250 to 499',
        '500+',
    ]),
    ('salary-range', [
        'Below £25,000',
        '£25,000 – £29,000',
        '£30,000 – £34,000',
        '£35,000 and above'
    ]),
    ('investment-project-stage', [
        'Prospect',
        'Assign PM',
        'Active',
        'Verify win',
        'Won'
    ]),
    ('fdi-value', [
        'Higher',
        'Good',
        'Standard',
    ]),
)

ordered_metadata_view_test_ids = (
    'turnover',
    'employee-range',
    'salary-range',
    'investment-project-stage',
    'fdi-value',
)


@pytest.mark.parametrize('view_name,expected_names',
                         ordered_metadata_view_params,
                         ids=ordered_metadata_view_test_ids)
def test_ordered_metadata_order_view(view_name, expected_names, api_client):
    """Test that turnover and no. of employee ranges are returned in order.

    The response elements should be ordered according to the order column in the model.
    """
    url = reverse(viewname=view_name)
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    response_names = [value['name'] for value in response.json()]
    assert response_names == expected_names


def test_team_view(api_client):
    """
    Test that the team view returns role, uk_region and country as well.
    """
    url = reverse(viewname='team')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0] == {
        'id': 'cff02898-9698-e211-a939-e4115bead28a',
        'name': 'Aberdeen City Council',
        'role': {
            'name': 'ATO',
            'id': '846cb21e-6095-e211-a939-e4115bead28a'
        },
        'uk_region': None,
        'country': {
            'name': 'United Kingdom',
            'id': '80756b9a-5d95-e211-a939-e4115bead28a'
        }
    }
