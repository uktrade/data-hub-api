from datetime import datetime
from uuid import uuid4

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.test.factories import ArchivedCompanyFactory, CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.user.company_list.models import CompanyListItem
from datahub.user.company_list.views import CANT_ADD_ARCHIVED_COMPANY_MESSAGE


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
    """Tests for the GET method in CompanyListItemView."""

    def test_with_item_on_list(self):
        """Test that a 204 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        CompanyListItem.objects.create(adviser=self.user, company=company)

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
    Tests for the HEAD method in CompanyListItemView.

    These are the same as GET, but without response bodies.
    """

    def test_with_item_on_list(self):
        """Test that a 204 is returned if the company is on the authenticated user's list."""
        company = CompanyFactory()
        CompanyListItem.objects.create(adviser=self.user, company=company)

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
    """Tests for the PUT method in CompanyListItemView."""

    def test_with_new_item(self):
        """Test that a company can be added to the authenticated user's list."""
        company = CompanyFactory()
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert CompanyListItem.objects.filter(adviser=self.user, company=company).exists()

    def test_with_existing_item(self):
        """
        Test that no error is returned if the specified company is already on the
        authenticated user's list.
        """
        creation_date = datetime(2018, 1, 2, tzinfo=utc)
        modified_date = datetime(2018, 1, 2, tzinfo=utc)
        company = CompanyFactory()

        with freeze_time(creation_date):
            CompanyListItem.objects.create(adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})

        with freeze_time(modified_date):
            response = self.api_client.put(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''

        company_list_item = CompanyListItem.objects.get(adviser=self.user, company=company)
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
    """Tests for the DELETE method in CompanyListItemView."""

    def test_with_existing_item(self):
        """Test that a company can be removed from the authenticated user's list."""
        company = CompanyFactory()
        CompanyListItem.objects.create(adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(adviser=self.user, company=company).exists()

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
        assert not CompanyListItem.objects.filter(adviser=self.user, company=company).exists()

    def test_with_archived_company(self):
        """Test that no error is returned when removing an archived company."""
        company = ArchivedCompanyFactory()
        CompanyListItem.objects.create(adviser=self.user, company=company)

        url = reverse('api-v4:company-list:item', kwargs={'company_pk': company.pk})
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b''
        assert not CompanyListItem.objects.filter(adviser=self.user, company=company).exists()

    def test_with_non_existent_company(self):
        """Test that a 404 is returned if the specified company ID is invalid."""
        url = reverse('api-v4:company-list:item', kwargs={'company_pk': uuid4()})
        response = self.api_client.put(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
