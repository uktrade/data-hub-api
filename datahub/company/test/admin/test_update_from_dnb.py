from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.messages import get_messages
from django.urls import reverse
from rest_framework import status
from reversion.models import Version

from datahub.company.models import Company, CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user


DNB_SEARCH_URL = urljoin(f'{settings.DNB_SERVICE_BASE_URL}/', 'companies/search/')


@pytest.fixture
def dnb_response():
    """
    Minimal valid DNB response
    """
    return {
        'results': [
            {
                'address_line_1': '10 Fake Drive',
                'address_line_2': '',
                'address_postcode': 'AB0 1CD',
                'address_town': 'London',
                'address_county': '',
                'address_country': 'GB',
                'registered_address_line_1': '11 Fake Drive',
                'registered_address_line_2': '',
                'registered_address_postcode': 'AB0 2CD',
                'registered_address_town': 'London',
                'registered_address_county': '',
                'registered_address_country': 'GB',
                'domain': 'foo.com',
                'duns_number': '123456789',
                'primary_name': 'FOO BICYCLES LIMITED',
                'trading_names': [],
                'registration_numbers': [
                    {
                        'registration_number': '012345',
                        'registration_type': 'uk_companies_house_number',
                    },
                ],
                'global_ultimate_duns_number': '987654321',
            },
        ],
    }


class TestUpdateFromDNB(AdminTestMixin):
    """
    Tests GET requests to 'Update from DNB'.
    """

    def _create_company(self, **kwargs):
        self.company = CompanyFactory(**kwargs)
        change_url = reverse(
            admin_urlname(Company._meta, 'change'),
            args=(self.company.pk, ),
        )
        update_url = reverse(
            admin_urlname(Company._meta, 'update-from-dnb'),
            args=(self.company.pk, ),
        )
        return (change_url, update_url)

    def test_get(self, requests_mock, dnb_response):
        """
        Test that the link exists for a company with duns_number
        and a user with the change company permission.
        """
        change_url, update_url = self._create_company(duns_number='123456789')
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        response = self.client.get(change_url)
        assert update_url in response.rendered_content
        response = self.client.get(update_url)
        response.status_code == status.HTTP_200_OK

    def test_get_view_permission_only(self):
        """
        Test that the link does not exist for a company with duns_number
        but a user with only the view company permission.
        """
        change_url, update_url = self._create_company(duns_number='123456789')
        user = create_test_user(
            permission_codenames=(CompanyPermission.view_company,),
            is_staff=True,
            password=self.PASSWORD,
        )
        client = self.create_client(user=user)
        response = client.get(change_url)
        assert update_url not in response.rendered_content
        response = client.get(update_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_no_duns_number(self):
        """
        Test that the link does not exist when the company does not
        have a duns_number.
        """
        change_url, update_url = self._create_company()
        response = self.client.get(change_url)
        assert update_url not in response.rendered_content
        response = self.client.get(update_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post(self, requests_mock, dnb_response):
        """
        Test that a post request to 'upddate-from-dnb' updates
        the company.
        """
        _, update_url = self._create_company(
            duns_number='123456789',
            pending_dnb_investigation=True,
        )
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        response = self.client.post(update_url)
        assert response.status_code == status.HTTP_302_FOUND

        self.company.refresh_from_db()
        dnb_company = dnb_response['results'][0]

        assert self.company.name == dnb_company['primary_name']
        assert self.company.address_1 == dnb_company['address_line_1']
        assert self.company.address_2 == dnb_company['address_line_2']
        assert self.company.address_town == dnb_company['address_town']
        assert self.company.address_county == dnb_company['address_county']
        assert self.company.address_country.iso_alpha2_code == dnb_company['address_country']
        assert not self.company.pending_dnb_investigation
        assert (
            self.company.global_ultimate_duns_number
            == dnb_company['global_ultimate_duns_number']
        )

        versions = list(Version.objects.get_for_object(self.company))
        assert len(versions) == 1
        assert versions[0].revision.comment == 'Updated from D&B'

    @pytest.mark.parametrize(
        'dnb_response_code',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_post_dnb_error(self, requests_mock, dnb_response_code):
        """
        Tests that the users get an error message if the dnb-service
        doesn't return with a 200 status code.
        """
        _, update_url = self._create_company(duns_number='123456789')
        requests_mock.post(
            DNB_SEARCH_URL,
            status_code=dnb_response_code,
        )
        response = self.client.post(update_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == 'Something went wrong in an upstream service.'

    @pytest.mark.parametrize(
        'search_results, expected_message',
        (
            (
                [],
                'No matching company found in D&B database.',
            ),
            (
                ['foo', 'bar'],
                'Something went wrong in an upstream service.',
            ),
            (
                [{'duns_number': '012345678'}],
                'Something went wrong in an upstream service.',
            ),
        ),
    )
    def test_post_dnb_response_invalid(
        self,
        requests_mock,
        search_results,
        expected_message,
    ):
        """
        Test if we get anything other than a single company from dnb-service,
        we return an error message to the user.
        """
        _, update_url = self._create_company(duns_number='123456789')
        requests_mock.post(
            DNB_SEARCH_URL,
            json={'results': search_results},
        )
        response = self.client.post(update_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == expected_message

    def test_post_dnb_data_invalid(
        self,
        requests_mock,
        dnb_response,
    ):
        """
        Tests that if the data returned from DNB does not
        clear DataHub validation, we show an appropriate
        message to our users.
        """
        _, update_url = self._create_company(duns_number='123456789')
        dnb_response['results'][0]['primary_name'] = None
        requests_mock.post(
            DNB_SEARCH_URL,
            json=dnb_response,
        )
        response = self.client.post(update_url)
        assert response.status_code == status.HTTP_302_FOUND

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert str(messages[0]) == 'Data from D&B did not pass the Data Hub validation checks.'
