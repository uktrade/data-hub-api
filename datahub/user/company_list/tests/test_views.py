from random import sample

import factory
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.user.company_list.models import CompanyList
from datahub.user.company_list.tests.factories import CompanyListFactory


list_collection_url = reverse('api-v4:company-list:list-collection')


class TestListCompanyListsView(APITestMixin):
    """Tests for listing a user's company lists."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.get(list_collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_companylist'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        response = api_client.get(list_collection_url)
        assert response.status_code == expected_status

    def test_returns_empty_list_when_no_lists(self):
        """Test that no results are returned when the user has no company lists."""
        response = self.api_client.get(list_collection_url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_doesnt_return_other_users_lists(self):
        """Test that other users' company lists are not returned."""
        # Create some lists belonging to other users
        CompanyListFactory.create_batch(5)

        response = self.api_client.get(list_collection_url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_returns_items_in_expected_format(self):
        """Test that a user's list is returned in the expected format."""
        company_list = CompanyListFactory(adviser=self.user)

        response = self.api_client.get(list_collection_url)
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == 1
        assert results[0] == {
            'id': str(company_list.pk),
            'name': company_list.name,
            'created_on': format_date_or_datetime(company_list.created_on),
        }

    def test_lists_are_sorted_by_name(self):
        """Test that returned lists are sorted by name."""
        expected_list_names = ['A list', 'B list', 'C list', 'D list']

        shuffled_list_names = sample(expected_list_names, len(expected_list_names))
        CompanyListFactory.create_batch(
            len(expected_list_names),
            adviser=self.user,
            name=factory.Iterator(shuffled_list_names),
        )

        response = self.api_client.get(list_collection_url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        actual_list_names = [result['name'] for result in response_data['results']]
        assert actual_list_names == expected_list_names


class TestAddCompanyListView(APITestMixin):
    """Tests for adding a company list."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        response = api_client.post(list_collection_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['add_companylist'], status.HTTP_201_CREATED),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        api_client = self.create_api_client(user=user)
        response = api_client.post(
            list_collection_url,
            data={
                'name': 'test list',
            },
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'request_data,expected_errors',
        (
            pytest.param(
                {},
                {
                    'name': ['This field is required.'],
                },
                id='name omitted',
            ),
            pytest.param(
                {
                    'name': None,
                },
                {
                    'name': ['This field may not be null.'],
                },
                id='name is null',
            ),
            pytest.param(
                {
                    'name': '',
                },
                {
                    'name': ['This field may not be blank.'],
                },
                id='name is empty string',
            ),
        ),
    )
    def test_validation(self, request_data, expected_errors):
        """Test validation."""
        response = self.api_client.post(list_collection_url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    @freeze_time('2017-04-19 15:25:30.986208')
    def test_successfully_create_a_list(self):
        """Test that a list can be created."""
        name = 'list a'
        response = self.api_client.post(
            list_collection_url,
            data={
                'name': name,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'name': name,
            'created_on': '2017-04-19T15:25:30.986208Z',
        }

        company_list = CompanyList.objects.get(pk=response_data['id'])

        # adviser should be set to the authenticated user
        assert company_list.adviser == self.user
        assert company_list.created_by == self.user
        assert company_list.modified_by == self.user
