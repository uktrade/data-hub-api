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

from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.user.company_list.models import CompanyList, CompanyListItem
from datahub.user.company_list.tests.factories import (
    CompanyListFactory,
    LegacyCompanyListItemFactory,
)
from datahub.user.company_list.views import (
    CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
    DEFAULT_LEGACY_LIST_NAME,
)


def company_with_interactions_factory(num_interactions):
    """Factory for a company with interactions."""
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    return company


class TestCompanyListView(APITestMixin):
    """Tests for CompanyListView."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned for an unauthenticated user."""
        url = reverse('api-v4:company-list:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client):
        """Test that a 403 is returned for a user with no permissions."""
        user = create_test_user(dit_team=TeamFactory())

        url = reverse('api-v4:company-list:collection')
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_no_list_items(self):
        """
        Test that an empty list is returned if the user does not have any companies on their
        list.
        """
        url = reverse('api-v4:company-list:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_with_only_items_on_other_users_list(self):
        """
        Test that an empty list is returned if the user has no companies on their list,
        but other users have companies on theirs.
        """
        LegacyCompanyListItemFactory.create_batch(5)

        url = reverse('api-v4:company-list:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    @pytest.mark.parametrize(
        'company_factory',
        (
            CompanyFactory,
            ArchivedCompanyFactory,
            partial(company_with_interactions_factory, 1),
            partial(company_with_interactions_factory, 10),
        ),
    )
    def test_with_item(self, company_factory):
        """Test serialisation of various companies."""
        company = company_factory()
        list_item = LegacyCompanyListItemFactory(list__adviser=self.user, company=company)

        latest_interaction = company.interactions.order_by('-date', '-created_by', 'pk').first()

        url = reverse('api-v4:company-list:collection')
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
        interaction_dates = [
            datetime(2019, 10, 8, tzinfo=utc),
            datetime(2016, 9, 7, tzinfo=utc),
            datetime(2009, 5, 6, tzinfo=utc),
            None,
        ]
        shuffled_dates = sample(interaction_dates, len(interaction_dates))
        company_list = CompanyListFactory(adviser=self.user, is_legacy_default=True)
        list_items = LegacyCompanyListItemFactory.create_batch(
            len(interaction_dates),
            list=company_list,
        )

        for interaction_date, list_item in zip(shuffled_dates, list_items):
            if interaction_date:
                CompanyInteractionFactory(date=interaction_date, company=list_item.company)

        url = reverse('api-v4:company-list:collection')

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


@pytest.mark.parametrize('http_method', ('delete', 'get', 'head', 'put'))
class TestCompanyListItemAuth(APITestMixin):
    """Tests authentication and authorisation for the company list item views."""

    def test_returns_401_if_unauthenticated(self, api_client, http_method):
        """Test that a 401 is returned for an unauthenticated user."""
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client, http_method):
        """Test that a 403 is returned for a user with no permissions."""
        company = CompanyFactory()
        user = create_test_user(dit_team=TeamFactory())

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        api_client = self.create_api_client(user=user)
        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetCompanyListItemView(APITestMixin):
    """Tests for the GET method in LegacyCompanyListItemView."""

    def test_with_item_on_list(self):
        """Test that a 204 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        LegacyCompanyListItemFactory(list__adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

    def test_with_item_not_on_list(self):
        """Test that a 404 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            'detail': 'Not found.',
        }

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the company does not exist."""
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': uuid4()})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {
            'detail': 'Not found.',
        }


class TestHeadCompanyListItemView(APITestMixin):
    """
    Tests for the HEAD method in LegacyCompanyListItemView.

    These are the same as GET, but without response bodies.
    """

    def test_with_item_on_list(self):
        """Test that a 204 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        LegacyCompanyListItemFactory(list__adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.head(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

    def test_with_item_not_on_list(self):
        """Test that a 404 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.head(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b''

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the company does not exist."""
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': uuid4()})
        response = self.api_client.head(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b''


class TestCreateOrUpdateCompanyListItemView(APITestMixin):
    """Tests for the PUT method in LegacyCompanyListItemView."""

    def test_creates_new_items(self):
        """Test that a company can be added to the authenticated user's list."""
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        list_item = CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        ).first()

        assert list_item
        assert list_item.adviser == self.user
        assert list_item.created_by == self.user
        assert list_item.modified_by == self.user

    def test_creates_a_legacy_list_when_adding_a_new_item(self):
        """
        Test that when a list item is added, a legacy default list is created when it didn't
        already exist.
        """
        # Existing company lists for other users should not matter
        unrelated_lists = CompanyListFactory.create_batch(5, is_legacy_default=True)
        company = CompanyFactory()

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_item = CompanyListItem.objects.get(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        )
        list_ = list_item.list
        assert list_
        assert list_.name == DEFAULT_LEGACY_LIST_NAME
        assert list_.adviser == self.user
        assert list_.created_by == self.user
        assert list_.modified_by == self.user

        assert CompanyList.objects.count() == len(unrelated_lists) + 1

    def test_reuses_an_existing_legacy_list_when_adding_a_new_item(self):
        """Test that when a list item is added, an existing legacy default list is reused."""
        existing_list_name = 'existing list'
        CompanyListFactory(adviser=self.user, is_legacy_default=True, name=existing_list_name)
        company = CompanyFactory()

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_item = CompanyListItem.objects.get(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        )
        list_ = list_item.list
        assert list_
        assert list_.is_legacy_default
        assert list_.name == existing_list_name

        assert CompanyList.objects.count() == 1

    def test_does_not_overwrite_other_items(self):
        """Test that adding an item does not overwrite other (unrelated) items."""
        existing_companies = CompanyFactory.create_batch(5)
        company_list = CompanyListFactory(adviser=self.user, is_legacy_default=True)
        LegacyCompanyListItemFactory.create_batch(
            5,
            list=company_list,
            company=factory.Iterator(existing_companies),
        )
        company_to_add = CompanyFactory()

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company_to_add.pk})
        response = self.api_client.put(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_item_queryset = CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
        )
        companies_after = {item.company for item in list_item_queryset}
        assert companies_after == {*existing_companies, company_to_add}

    def test_two_advisers_can_have_the_same_company(self):
        """Test that two advisers can have the same company on their list."""
        other_user_item = LegacyCompanyListItemFactory()
        other_user = other_user_item.list.adviser
        company = other_user_item.company

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert CompanyListItem.objects.filter(
            list__adviser=other_user,
            list__is_legacy_default=True,
            company=company,
        ).exists()
        assert CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        ).exists()

    def test_with_existing_item(self):
        """
        Test that no error is returned if the specified company is already on the
        authenticated user's list.
        """
        creation_date = datetime(2018, 1, 2, tzinfo=utc)
        modified_date = datetime(2018, 1, 2, tzinfo=utc)
        company = CompanyFactory()

        with freeze_time(creation_date):
            LegacyCompanyListItemFactory(
                company=company,
                list__adviser=self.user,
                list__is_legacy_default=True,
            )

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})

        with freeze_time(modified_date):
            response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        company_list_item = CompanyListItem.objects.get(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        )
        assert company_list_item.created_on == creation_date
        assert company_list_item.modified_on == modified_date

    def test_with_archived_company(self):
        """Test that an archived company can't be added to the authenticated user's list."""
        company = ArchivedCompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
        }

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the specified company ID is invalid."""
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': uuid4()})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteCompanyListItemView(APITestMixin):
    """Tests for the DELETE method in LegacyCompanyListItemView."""

    def test_with_existing_item(self):
        """Test that a company can be removed from the authenticated user's list."""
        company = CompanyFactory()
        LegacyCompanyListItemFactory(list__adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        ).exists()

    def test_with_new_item(self):
        """
        Test that no error is returned if the specified company was not on the
        authenticated user's list.
        """
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        ).exists()

    def test_with_archived_company(self):
        """Test that no error is returned when removing an archived company."""
        company = ArchivedCompanyFactory()
        LegacyCompanyListItemFactory(list__adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__is_legacy_default=True,
            company=company,
        ).exists()

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the specified company ID is invalid."""
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': uuid4()})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
