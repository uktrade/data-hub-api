from random import sample
from uuid import uuid4

import factory
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.user.company_list.models import CompanyList, CompanyListItem
from datahub.user.company_list.test.factories import CompanyListFactory, CompanyListItemFactory


list_collection_url = reverse('api-v4:company-list:list-collection')


def _get_list_detail_url(list_pk):
    return reverse('api-v4:company-list:list-detail', kwargs={'pk': list_pk})


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

    def test_filter_by_invalid_company_id(self):
        """
        Test that an error is returned when trying to filter by a company ID that is not a
        valid UUID.
        """
        response = self.api_client.get(
            list_collection_url,
            data={
                'items__company_id': 'invalid_id',
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'items__company_id': ["'invalid_id' is not a valid UUID."],
        }

    def test_can_filter_by_valid_company_id(self):
        """Test that a user's lists can be filtered to those containing a particular company."""
        company_to_filter_by = CompanyFactory()

        # Create some lists containing `company_to_filter_by`
        expected_lists = CompanyListFactory.create_batch(3, adviser=self.user)
        CompanyListItemFactory.create_batch(
            len(expected_lists),
            list=factory.Iterator(expected_lists),
            company=company_to_filter_by,
        )

        # Create some lists without `company_to_filter_by` that should not be returned
        CompanyListFactory.create_batch(3, adviser=self.user)

        response = self.api_client.get(
            list_collection_url,
            data={
                'items__company_id': company_to_filter_by.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        assert len(results) == len(expected_lists)

        expected_list_ids = {str(list_.pk) for list_ in expected_lists}
        actual_list_ids = {result['id'] for result in results}
        assert actual_list_ids == expected_list_ids

    def test_returns_no_lists_if_filtered_by_company_not_on_a_list(self):
        """
        Test that no lists are returned when filtering lists by a company not on any of the
        authenticated user's lists.
        """
        # Create some lists and list items for the user
        CompanyListItemFactory.create_batch(5, list__adviser=self.user)

        # Filter by a company not on a list
        response = self.api_client.get(
            list_collection_url,
            data={
                'items__company_id': CompanyFactory().pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['results'] == []

    def test_filtering_by_company_id_doesnt_return_other_users_lists(self):
        """Test that filtering by company ID doesn't return other users' lists."""
        # Create a list item belonging to another user
        list_item = CompanyListItemFactory()

        response = self.api_client.get(
            list_collection_url,
            data={
                'items__company_id': list_item.company.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['results'] == []


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


class TestUpdateCompanyListView(APITestMixin):
    """Tests for renaming a company list."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        url = _get_list_detail_url(uuid4())

        response = api_client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['change_companylist'], status.HTTP_200_OK),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        company_list = CompanyListFactory(adviser=user)
        url = _get_list_detail_url(company_list.pk)

        api_client = self.create_api_client(user=user)
        response = api_client.patch(
            url,
            data={
                'name': 'test list',
            },
        )
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'request_data,expected_errors',
        (
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
        company_list = CompanyListFactory(adviser=self.user)
        url = _get_list_detail_url(company_list.pk)
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_errors

    def test_can_successfully_rename_a_list(self):
        """Test that a list can be renamed."""
        company_list = CompanyListFactory(adviser=self.user, name='old name')
        url = _get_list_detail_url(company_list.pk)

        new_name = 'new name'
        response = self.api_client.patch(
            url,
            data={
                'name': new_name,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'id': str(company_list.pk),
            'name': new_name,
            'created_on': format_date_or_datetime(company_list.created_on),
        }

        company_list.refresh_from_db()
        assert company_list.name == new_name

    def test_cannot_rename_another_users_list(self):
        """Test that another user's list can't be renamed."""
        company_list = CompanyListFactory(name='old name')
        url = _get_list_detail_url(company_list.pk)

        new_name = 'new name'
        response = self.api_client.patch(
            url,
            data={
                'name': new_name,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteCompanyListView(APITestMixin):
    """Tests for deleting a company list."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        url = _get_list_detail_url(uuid4())

        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['delete_companylist'], status.HTTP_204_NO_CONTENT),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status, api_client):
        """Test that the expected status is returned for various user permissions."""
        user = create_test_user(permission_codenames=permission_codenames, dit_team=None)
        company_list = CompanyListFactory(adviser=user)
        url = _get_list_detail_url(company_list.pk)

        api_client = self.create_api_client(user=user)
        response = api_client.delete(url)
        assert response.status_code == expected_status

    def test_can_delete_a_list(self):
        """Test that a list (including its items) can be deleted."""
        company_list = CompanyListFactory(adviser=self.user)
        list_item = CompanyListItemFactory(list=company_list)

        url = _get_list_detail_url(company_list.pk)

        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        with pytest.raises(CompanyListItem.DoesNotExist):
            list_item.refresh_from_db()

        # The company should not be deleted
        assert Company.objects.filter(pk=list_item.company.pk).exists()

    def test_other_lists_are_not_affected(self):
        """Test that other lists are not affected when a list is deleted."""
        list_to_delete = CompanyListFactory(adviser=self.user)
        list_item = CompanyListItemFactory(list=list_to_delete)

        other_list = CompanyListFactory(adviser=self.user)
        other_list_item = CompanyListItemFactory(company=list_item.company)

        url = _get_list_detail_url(list_to_delete.pk)

        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        try:
            other_list.refresh_from_db()
            other_list_item.refresh_from_db()
        except (CompanyList.DoesNotExist, CompanyListItem.DoesNotExist):
            pytest.fail('Other lists should not be affected.')

    def test_cannot_delete_another_users_list(self):
        """Test that another user's list can't be deleted."""
        company_list = CompanyListFactory()
        url = _get_list_detail_url(company_list.pk)

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
