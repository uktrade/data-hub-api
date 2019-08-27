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
from datahub.user.company_list.models import CompanyListItem
from datahub.user.company_list.tests.factories import (
    CompanyListFactory,
    CompanyListItemFactory,
)
from datahub.user.company_list.views import (
    CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
)


def company_with_interactions_factory(num_interactions):
    """Factory for a company with interactions."""
    company = CompanyFactory()
    CompanyInteractionFactory.create_batch(num_interactions, company=company)
    return company


@pytest.mark.parametrize('http_method', ('delete', 'get', 'head', 'put'))
class TestCompanyListItemAuth(APITestMixin):
    """Tests authentication and authorisation for the company list item views."""

    def test_returns_401_if_unauthenticated(self, api_client, http_method):
        """Test that a 401 is returned for an unauthenticated user."""
        company = CompanyFactory()
        company_list = CompanyListFactory()
        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )
        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client, http_method):
        """Test that a 403 is returned for a user with no permissions."""
        company = CompanyFactory()
        user = create_test_user(dit_team=TeamFactory())
        company_list = CompanyListFactory(adviser=user)

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.generic(http_method, url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCreateOrUpdateCompanyListItemAPIView(APITestMixin):
    """Tests for the PUT method in CompanyListItemAPIView."""

    def test_creates_new_items(self):
        """Test that a company can be added to the authenticated user's list."""
        company = CompanyFactory()
        company_list = CompanyListFactory(adviser=self.user)

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )

        response = self.api_client.put(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        list_item = _get_queryset_for_list_adviser_and_company(
            company_list,
            self.user,
            company,
        ).first()

        assert list_item
        assert list_item.list.adviser == self.user
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

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company_to_add.pk,
            },
        )
        response = self.api_client.put(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        list_item_queryset = CompanyListItem.objects.filter(
            list=company_list,
            list__adviser=self.user,
        )
        companies_after = {item.company for item in list_item_queryset}
        assert companies_after == {*existing_companies, company_to_add}

    def test_two_advisers_can_have_the_same_company(self):
        """Test that two advisers can have the same company on their list."""
        other_user_item = CompanyListItemFactory()
        other_user = other_user_item.list.adviser
        company = other_user_item.company

        company_list = CompanyListFactory(adviser=self.user)

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )
        response = self.api_client.put(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert _get_queryset_for_list_adviser_and_company(
            other_user_item.list,
            other_user,
            company,
        ).exists()
        assert _get_queryset_for_list_adviser_and_company(
            company_list,
            self.user,
            company,
        ).exists()

    def test_adviser_can_have_the_same_company_on_multiple_lists(self):
        """Tests that adviser can have the same company on multiple lists."""
        company = CompanyFactory()
        lists = CompanyListFactory.create_batch(5, adviser=self.user)
        for company_list in lists:
            other_companies = CompanyFactory.create_batch(5)

            CompanyListItemFactory.create_batch(
                len(other_companies),
                list=company_list,
                company=factory.Iterator(other_companies),
            )

        for company_list in lists:
            url = reverse(
                'api-v4:company-list:list-item',
                kwargs={
                    'company_list_pk': company_list.pk,
                    'company_pk': company.pk,
                },
            )
            response = self.api_client.put(url)
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert response.content == b''

        assert CompanyListItem.objects.filter(
            list__adviser=self.user,
            list__in=lists,
            company=company,
        ).count() == 5

    def test_with_existing_item(self):
        """
        Test that no error is returned if the specified company is already on the
        authenticated user's list.
        """
        creation_date = datetime(2018, 1, 2, tzinfo=utc)
        modified_date = datetime(2018, 1, 2, tzinfo=utc)
        company = CompanyFactory()

        company_list = CompanyListFactory(adviser=self.user)

        with freeze_time(creation_date):
            CompanyListItemFactory(
                list=company_list,
                list__adviser=self.user,
                company=company,
            )

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )

        with freeze_time(modified_date):
            response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        company_list_item = _get_queryset_for_list_adviser_and_company(
            company_list,
            self.user,
            company,
        ).first()

        assert company_list_item.created_on == creation_date
        assert company_list_item.modified_on == modified_date

    def test_with_archived_company(self):
        """Test that an archived company can't be added to the authenticated user's list."""
        company_list = CompanyListItemFactory(adviser=self.user)
        company = ArchivedCompanyFactory()
        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': company.pk,
            },
        )
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            api_settings.NON_FIELD_ERRORS_KEY: CANT_ADD_ARCHIVED_COMPANY_MESSAGE,
        }

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the specified company ID is invalid."""
        company_list = CompanyListFactory(adviser=self.user)
        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': company_list.pk,
                'company_pk': uuid4(),
            },
        )
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_non_existent_list(self):
        """Test that you cannot add an item to a list that does not exist."""
        # Existing company lists for other users should not matter
        CompanyListFactory.create_batch(5)
        company = CompanyFactory()

        url = reverse(
            'api-v4:company-list:list-item',
            kwargs={
                'company_list_pk': uuid4(),
                'company_pk': company.pk,
            },
        )
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
        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': company_list.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_403_if_without_permissions(self, api_client):
        """Test that a 403 is returned for a user with no permissions."""
        user = create_test_user(dit_team=TeamFactory())
        company_list = CompanyListFactory(adviser=user)

        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': company_list.pk,
            },
        )
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_with_no_list_items(self):
        """
        Test that an empty list is returned if the user does not have any companies on their
        list.
        """
        company_list = CompanyListFactory(adviser=self.user)
        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': company_list.pk,
            },
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_with_list_that_does_not_exist(self):
        """
        Test that an empty list is returned if the user does not have any companies on their
        list.
        """
        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': uuid4(),
            },
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_with_only_items_on_other_users_list(self):
        """
        Test that an empty list is returned if the user has no companies on their list,
        but other users have companies on theirs.
        """
        CompanyListItemFactory.create_batch(5)
        company_list = CompanyListFactory(adviser=self.user)
        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': company_list.pk,
            },
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['results'] == []

    def test_with_multiple_user_lists(self):
        """Test that user can list their own lists."""
        creation_date = datetime(2018, 1, 2, tzinfo=utc)

        # other items on other users lists, that shouldn't appear in results
        CompanyListItemFactory.create_batch(10)

        lists = CompanyListFactory.create_batch(5, adviser=self.user)

        company_list_companies = {}

        for company_list in lists:
            companies = CompanyFactory.create_batch(5)
            company_list_companies[company_list.pk] = companies

            with freeze_time(creation_date):
                CompanyListItemFactory.create_batch(
                    len(companies),
                    list=company_list,
                    company=factory.Iterator(companies),
                )

        for company_list in lists:
            url = reverse(
                'api-v4:company-list:list-collection',
                kwargs={
                    'company_list_pk': company_list.pk,
                },
            )
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
        ),
    )
    def test_with_item(self, company_factory):
        """Test serialisation of various companies."""
        company = company_factory()
        list_item = CompanyListItemFactory(list__adviser=self.user, company=company)

        latest_interaction = company.interactions.order_by('-date', '-created_by', 'pk').first()

        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': list_item.list.pk,
            },
        )
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
        company_list = CompanyListFactory(adviser=self.user)
        list_items = CompanyListItemFactory.create_batch(
            len(interaction_dates),
            list=company_list,
        )

        for interaction_date, list_item in zip(shuffled_dates, list_items):
            if interaction_date:
                CompanyInteractionFactory(date=interaction_date, company=list_item.company)

        url = reverse(
            'api-v4:company-list:list-collection',
            kwargs={
                'company_list_pk': company_list.pk,
            },
        )

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


def _get_queryset_for_list_adviser_and_company(company_list, adviser, company):
    return CompanyListItem.objects.filter(
        list=company_list,
        list__adviser=adviser,
        company=company,
    )
