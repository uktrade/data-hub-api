from datetime import datetime
from functools import partial
from random import sample
from uuid import uuid4

import factory
import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.models import Company
from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.user.company_list.models import CompanyList
from datahub.user.company_list.models import CompanyListItem
from datahub.user.company_list.test.factories import CompanyListFactory, CompanyListItemFactory
from datahub.user.company_list.views import (
    CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
)

list_collection_url = reverse('api-v4:company-list:list-collection')


def company_with_interactions_factory(num_interactions, **interaction_kwargs):
    """Factory for a company with interactions."""
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(num_interactions, company=company, **interaction_kwargs)
    return company


def company_with_multiple_participant_interaction_factory():
    """Factory for a company with an interaction that has multiple participants."""
    company = CompanyFactory()
    interaction = CompanyInteractionFactory(company=company, dit_participants=[])
    InteractionDITParticipantFactory.create_batch(2, interaction=interaction)
    return company


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
            'item_count': 0,
            'name': company_list.name,
            'created_on': format_date_or_datetime(company_list.created_on),
        }

    @pytest.mark.parametrize('num_items', (0, 5, 10))
    def test_includes_accurate_item_count(self, num_items):
        """Test that the correct item count is returned."""
        company_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory.create_batch(num_items, list=company_list)

        # Create some unrelated items – should not affect the count
        CompanyListItemFactory.create_batch(7)

        response = self.api_client.get(list_collection_url)
        assert response.status_code == status.HTTP_200_OK

        results = response.json()['results']
        result = next(result for result in results if result['id'] == str(company_list.pk))

        assert result['item_count'] == num_items

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
            'items__company_id': ['“invalid_id” is not a valid UUID.'],
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


class TestGetCompanyListView(APITestMixin):
    """Tests for getting a single company list."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        url = _get_list_detail_url(uuid4())

        response = api_client.get(url)
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
        company_list = CompanyListFactory(adviser=user)
        url = _get_list_detail_url(company_list.pk)

        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == expected_status

    def test_returns_404_if_list_doesnt_exist(self):
        """Test that a 404 is returned if the list ID doesn't exist."""
        url = _get_list_detail_url(uuid4())
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_can_get_a_list(self):
        """Test that details of a single list can be retrieved."""
        company_list = CompanyListFactory(adviser=self.user)
        url = _get_list_detail_url(company_list.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data == {
            'id': str(company_list.pk),
            'item_count': 0,
            'name': company_list.name,
            'created_on': format_date_or_datetime(company_list.created_on),
        }

    def test_cannot_get_another_users_list(self):
        """Test that another user's list can't be retrieved."""
        company_list = CompanyListFactory()
        url = _get_list_detail_url(company_list.pk)

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


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
            'item_count': 0,
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


@pytest.mark.parametrize('http_method', ('delete', 'put'))
class TestCompanyListItemAuth(APITestMixin):
    """Tests authentication and authorisation for the company list item views."""

    def test_returns_401_if_unauthenticated(self, api_client, http_method):
        """Test that a 401 is returned for an unauthenticated user."""
        company = CompanyFactory()
        company_list = CompanyListFactory()

        url = _get_list_item_url(company_list.pk, company.pk)
        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client, http_method):
        """Test that a 403 is returned for a user with no permissions."""
        company = CompanyFactory()
        user = create_test_user(dit_team=TeamFactory())
        company_list = CompanyListFactory(adviser=user)

        url = _get_list_item_url(company_list.pk, company.pk)
        api_client = self.create_api_client(user=user)

        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCreateOrUpdateCompanyListItemAPIView(APITestMixin):
    """Tests for the PUT method in CompanyListItemAPIView."""

    def test_creates_new_items(self):
        """Test that a company can be added to the authenticated user's list."""
        company = CompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        list_item = _get_queryset_for_list_and_company(company_list, company).first()

        assert list_item
        assert list_item.list == company_list
        assert list_item.created_by == self.user
        assert list_item.modified_by == self.user

    def test_does_not_overwrite_other_items(self):
        """Test that adding an item does not overwrite other (unrelated) items."""
        existing_companies = CompanyFactory.create_batch(5)
        company_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory.create_batch(
            5,
            list=company_list,
            company=factory.Iterator(existing_companies),
        )
        company_to_add = CompanyFactory()

        url = _get_list_item_url(company_list.pk, company_to_add.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_item_queryset = CompanyListItem.objects.filter(list=company_list)
        companies_after = {item.company for item in list_item_queryset}
        assert companies_after == {*existing_companies, company_to_add}

    def test_two_advisers_can_have_the_same_company(self):
        """Test that two advisers can have the same company on their list."""
        other_user_item = CompanyListItemFactory()
        company = other_user_item.company

        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert _get_queryset_for_list_and_company(other_user_item.list, company).exists()
        assert _get_queryset_for_list_and_company(company_list, company).exists()

    def test_adviser_can_have_the_same_company_on_multiple_lists(self):
        """Tests that adviser can have the same company on multiple lists."""
        company = CompanyFactory()

        other_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory(list=other_list, company=company)

        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        assert CompanyListItem.objects.filter(
            list__in=(other_list, company_list),
            company=company,
        ).count() == 2

    def test_with_existing_item(self):
        """
        Test that no error is returned if the specified company is already on the
        authenticated user's list.
        """
        creation_date = datetime(2018, 1, 2, tzinfo=utc)
        modified_date = datetime(2018, 1, 5, tzinfo=utc)
        company = CompanyFactory()

        company_list = CompanyListFactory(adviser=self.user)

        with freeze_time(creation_date):
            CompanyListItemFactory(list=company_list, company=company)

        url = _get_list_item_url(company_list.pk, company.pk)

        with freeze_time(modified_date):
            response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        company_list_item = _get_queryset_for_list_and_company(
            company_list,
            company,
        ).first()

        assert company_list_item.created_on == creation_date
        assert company_list_item.modified_on == creation_date

    def test_with_archived_company(self):
        """Test that an archived company can't be added to the authenticated user's list."""
        company_list = CompanyListFactory(adviser=self.user)
        company = ArchivedCompanyFactory()

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
        }

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the specified company ID is invalid."""
        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_url(company_list.pk, uuid4())
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_non_existent_list(self):
        """Test that you cannot add an item to a list that does not exist."""
        # Existing company lists for other users should not matter
        CompanyListFactory.create_batch(5)
        company = CompanyFactory()

        url = _get_list_item_url(uuid4(), company.pk)
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not CompanyListItem.objects.filter(
            list__adviser=self.user,
            company=company,
        ).exists()


class TestCompanyListItemViewSet(APITestMixin):
    """Tests for CompanyListItemViewSet."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned for an unauthenticated user."""
        company_list = CompanyListFactory()

        url = _get_list_item_collection_url(company_list.pk)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client):
        """Test that a 403 is returned for a user with no permissions."""
        user = create_test_user(dit_team=TeamFactory())
        company_list = CompanyListFactory(adviser=user)

        api_client = self.create_api_client(user=user)

        url = _get_list_item_collection_url(company_list.pk)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_no_list_items(self):
        """
        Test that an empty list is returned if the user does not have any companies on the
        selected list.
        """
        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_collection_url(company_list.pk)
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_with_list_that_does_not_exist(self):
        """Test that 404 status is returned if selected list does not exist."""
        url = _get_list_item_collection_url(uuid4())
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_list_that_does_not_belong_to_user(self):
        """Test that 404 status is returned if selected list does not belong to user."""
        company_list = CompanyListFactory()
        url = _get_list_item_collection_url(company_list.pk)
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_only_items_on_other_users_lists(self):
        """
        Test that an empty list is returned if the user has no companies on their selected list,
        but other users have companies on theirs.
        """
        CompanyListItemFactory.create_batch(5)

        company_list = CompanyListFactory(adviser=self.user)

        url = _get_list_item_collection_url(company_list.pk)
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_with_multiple_user_lists(self):
        """Test that user who owns multiple lists can list all their contents."""
        lists = CompanyListFactory.create_batch(5, adviser=self.user)

        company_list_companies = {}

        # add multiple companies to user's lists
        for company_list in lists:
            companies = CompanyFactory.create_batch(5)
            company_list_companies[company_list.pk] = companies

            CompanyListItemFactory.create_batch(
                len(companies),
                list=company_list,
                company=factory.Iterator(companies),
            )

        # check if contents of each user's list can be listed
        for company_list in lists:
            url = _get_list_item_collection_url(company_list.pk)
            response = self.api_client.get(url)

            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()

            result_company_ids = {result['company']['id'] for result in response_data['results']}
            assert result_company_ids == {
                str(company.id) for company in company_list_companies[company_list.pk]
            }

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyFactory,
            ArchivedCompanyFactory,
            partial(company_with_interactions_factory, 1),
            partial(company_with_interactions_factory, 10),
            company_with_multiple_participant_interaction_factory,
            # Interaction participant with missing team
            partial(company_with_interactions_factory, 1, dit_participants__team=None),
            # Interaction participant with missing adviser
            partial(
                company_with_interactions_factory,
                1,
                dit_participants__adviser=None,
                dit_participants__team=factory.SubFactory(TeamFactory),
            ),
            # Interaction with no participants
            partial(company_with_interactions_factory, 1, dit_participants=[]),
        ),
    )
    def test_with_item(self, company_factory):
        """Test serialisation of various companies."""
        company = company_factory()
        list_item = CompanyListItemFactory(list__adviser=self.user, company=company)

        latest_interaction = company.interactions.order_by('-date', '-created_by', 'pk').first()

        url = _get_list_item_collection_url(list_item.list.pk)
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == [
            {
                'company': {
                    'id': str(company.pk),
                    'archived': company.archived,
                    'name': company.name,
                    'trading_names': company.trading_names,
                },
                'created_on': format_date_or_datetime(list_item.created_on),
                'latest_interaction': {
                    'id': str(latest_interaction.pk),
                    'created_on': format_date_or_datetime(latest_interaction.created_on),
                    'date': format_date_or_datetime(latest_interaction.date.date()),
                    'subject': latest_interaction.subject,
                    'dit_participants': [
                        {
                            'adviser': {
                                'id': str(dit_participant.adviser.pk),
                                'name': dit_participant.adviser.name,
                            } if dit_participant.adviser else None,
                            'team': {
                                'id': str(dit_participant.team.pk),
                                'name': dit_participant.team.name,
                            } if dit_participant.team else None,
                        }
                        for dit_participant in latest_interaction.dit_participants.order_by('pk')
                    ],
                } if latest_interaction else None,
            },
        ]

    def test_sorting(self):
        """
        Test that list items are sorted in reverse order of the date of the latest
        interaction with the company.
        Note that we want companies without any interactions to be sorted last.
        """
        # These dates are in the order we expect them to be returned
        # `None` represents a company without any interactions
        interaction_dates = [
            datetime(2019, 10, 8, tzinfo=utc),
            datetime(2016, 9, 7, tzinfo=utc),
            datetime(2009, 5, 6, tzinfo=utc),
            None,
        ]
        shuffled_dates = sample(interaction_dates, len(interaction_dates))
        company_list = CompanyListFactory(adviser=self.user)
        list_items = CompanyListItemFactory.create_batch(len(interaction_dates), list=company_list)

        for interaction_date, list_item in zip(shuffled_dates, list_items):
            if interaction_date:
                CompanyInteractionFactory(date=interaction_date, company=list_item.company)

        url = _get_list_item_collection_url(company_list.pk)

        # Make sure future interactions are also sorted correctly
        with freeze_time('2017-12-11 09:00:00'):
            response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        assert len(results) == len(interaction_dates)

        actual_interaction_dates = [
            result['latest_interaction']['date'] if result['latest_interaction'] else None
            for result in results
        ]
        expected_interaction_dates = [
            format_date_or_datetime(date_.date()) if date_ else None
            for date_ in interaction_dates
        ]
        assert actual_interaction_dates == expected_interaction_dates


class TestDeleteCompanyListItemAPIView(APITestMixin):
    """Tests for the DELETE method in CompanyListItemAPIView."""

    def test_with_existing_item(self):
        """Test that a company can be removed from the authenticated user's selected list."""
        company = CompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory(list=company_list, company=company)

        assert CompanyListItem.objects.filter(list=company_list, company=company).exists()

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        assert not CompanyListItem.objects.filter(list=company_list, company=company).exists()

    def test_with_company_not_on_the_list(self):
        """
        Test that 204 status is returned if company is not on the authenticated user's
        selected list.
        """
        company = CompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)
        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(list=company_list, company=company).exists()

    def test_with_company_that_does_not_exist(self):
        """Test that 404 status code is returned if the specified company does not exist."""
        company_list = CompanyListFactory(adviser=self.user)
        url = _get_list_item_url(company_list.pk, uuid4())
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b'{"detail":"Not found."}'

    def test_with_archived_company(self):
        """Test that no error is returned when removing an archived company."""
        company = ArchivedCompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory(list=company_list, company=company)

        assert CompanyListItem.objects.filter(list=company_list, company=company).exists()

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(list=company_list, company=company).exists()

    def test_that_actual_company_is_not_deleted(self):
        """
        Test that a company is not removed from database after removing from user's selected list.
        """
        company = CompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)
        CompanyListItemFactory(list=company_list, company=company)

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(list=company_list, company=company).exists()
        assert Company.objects.filter(pk=company.pk).exists()

    def test_with_list_that_does_not_belong_to_user(self):
        """Test that a company cannot be removed from another user's lists."""
        company = CompanyFactory()
        company_list = CompanyListFactory()
        CompanyListItemFactory(list=company_list, company=company)

        url = _get_list_item_url(company_list.pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b'{"detail":"Not found."}'

        # company has not been deleted from another user list
        assert CompanyListItem.objects.filter(list=company_list, company=company).exists()

    def test_with_list_that_does_not_exist(self):
        """Test that a company cannot be removed from a list that doesn't exist."""
        company = CompanyFactory()

        url = _get_list_item_url(uuid4(), company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b'{"detail":"Not found."}'

    def test_with_multiple_lists(self):
        """Test that deleting company from one list will not delete it from the other lists."""
        company = CompanyFactory()
        company_lists = CompanyListFactory.create_batch(5, adviser=self.user)

        CompanyListItemFactory.create_batch(
            5,
            list=factory.Iterator(company_lists),
            company=company,
        )

        # company exists on 5 user's lists
        assert CompanyListItem.objects.filter(list__in=company_lists, company=company).count() == 5

        url = _get_list_item_url(company_lists[0].pk, company.pk)
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        assert not CompanyListItem.objects.filter(list=company_lists[0], company=company).exists()

        # The company exists on 4 other lists
        assert CompanyListItem.objects.filter(list__in=company_lists, company=company).count() == 4


def _get_queryset_for_list_and_company(company_list, company):
    return CompanyListItem.objects.filter(list=company_list, company=company)


def _get_list_item_url(company_list_pk, company_pk):
    return reverse(
        'api-v4:company-list:item-detail',
        kwargs={
            'company_list_pk': company_list_pk,
            'company_pk': company_pk,
        },
    )


def _get_list_item_collection_url(company_list_pk):
    return reverse(
        'api-v4:company-list:item-collection',
        kwargs={'company_list_pk': company_list_pk},
    )
