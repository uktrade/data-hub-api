import datetime
import json

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.interaction.models import InteractionPermission
from datahub.interaction.test.factories import CompanyInteractionFactory


@pytest.fixture()
def dnb_company_search_feature_flag():
    """
    Creates the dnb company search feature flag.
    """
    yield FeatureFlagFactory(code=FEATURE_FLAG_DNB_COMPANY_SEARCH)


@pytest.fixture()
def dnb_company_search_datahub_companies():
    """
    Creates Data Hub companies for hydrating DNB search results with.
    """
    # Company with no interactions
    CompanyFactory(duns_number='1234567', id='6083b732-b07a-42d6-ada4-c8082293285b')
    # Company with two interactions
    company = CompanyFactory(duns_number='7654321', id='6083b732-b07a-42d6-ada4-c99999999999')

    interaction_date = make_aware(
        datetime.datetime(year=2019, month=8, day=1, hour=16, minute=0, second=0),
    )
    latest_interaction = CompanyInteractionFactory(
        id='6083b732-b07a-42d6-ada4-222222222222',
        date=interaction_date,
        subject='Meeting with Joe Bloggs',
        company=company,
    )
    latest_interaction.created_on = interaction_date
    latest_interaction.save()

    older_interaction_date = make_aware(datetime.datetime(year=2018, month=8, day=1))
    older_interaction = CompanyInteractionFactory(
        id='6083b732-b07a-42d6-ada4-111111111111',
        date=older_interaction_date,
        subject='Meeting with John Smith',
        company=company,
    )
    older_interaction.created_on = older_interaction_date


class TestDNBCompanySearchAPI(APITestMixin):
    """
    DNB Company Search view test case.
    """

    @pytest.mark.parametrize(
        'request_data,response_status_code,upstream_response_content,response_data',
        (
            pytest.param(
                b'{"arg": "value"}',
                200,
                b'{"results":[{"duns_number":"9999999"}]}',
                {
                    'results': [
                        {
                            'dnb_company': {'duns_number': '9999999'},
                            'datahub_company': None,
                        },
                    ],
                },
                id='successful call to proxied API with company that cannot be hydrated',
            ),
            pytest.param(
                b'{"arg": "value"}',
                200,
                b'{"results":[{"duns_number":"1234567"}, {"duns_number":"7654321"}]}',
                {
                    'results': [
                        {
                            'dnb_company': {'duns_number': '1234567'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c8082293285b',
                                'latest_interaction': None,
                            },
                        },
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                                'latest_interaction': {
                                    'id': '6083b732-b07a-42d6-ada4-222222222222',
                                    'date': '2019-08-01',
                                    'created_on': '2019-08-01T16:00:00Z',
                                    'subject': 'Meeting with Joe Bloggs',
                                },
                            },
                        },
                    ],
                },
                id='successful call to proxied API with company that can be hydrated',
            ),
            pytest.param(
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
                {'error': 'msg'},
                id='proxied API returns a bad request',
            ),
            pytest.param(
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
                {'error': 'msg'},
                id='proxied API returns a server error',
            ),
        ),
    )
    def test_post(
        self,
        dnb_company_search_feature_flag,
        dnb_company_search_datahub_companies,
        requests_mock,
        request_data,
        response_status_code,
        upstream_response_content,
        response_data,
    ):
        """
        Test for POST proxy.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=response_status_code,
            content=upstream_response_content,
        )

        user = create_test_user(
            permission_codenames=[
                CompanyPermission.view_company,
                InteractionPermission.view_all,
            ],
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:dnb-api:company-search')
        response = api_client.post(
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert json.loads(response.content) == response_data
        assert requests_mock.last_request.body == request_data

    def test_post_no_feature_flag(self, requests_mock):
        """
        Test that POST fails with a 404 when the feature flag is unset.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(
            url,
            data={'foo': 'bar'},
            content_type='application/json',
        )

        assert response.status_code == 404
        assert requests_mock.called is False

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self, dnb_company_search_feature_flag):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        url = reverse('api-v4:dnb-api:company-search')
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                url,
                data={'foo': 'bar'},
                content_type='application/json',
            )

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
            ('application/json', status.HTTP_200_OK),
        ),
    )
    def test_content_type(
        self,
        dnb_company_search_feature_flag,
        requests_mock,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=status.HTTP_200_OK,
            content=b'{"results":[]}',
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(url, content_type=content_type)

        assert response.status_code == expected_status_code

    def test_unauthenticated_not_authorised(self, requests_mock, dnb_company_search_feature_flag):
        """
        Ensure that a non-authenticated request gets a 401.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
        )

        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(Authorization='foo')

        url = reverse('api-v4:dnb-api:company-search')
        response = unauthorised_api_client.post(
            url,
            data={'foo': 'bar'},
            content_type='application/json',
        )

        assert response.status_code == 401
        assert requests_mock.called is False

    @pytest.mark.parametrize(
        'response_status_code,upstream_response_content,response_data,permission_codenames',
        (
            pytest.param(
                200,
                b'{"results":[{"duns_number":"7654321"}]}',
                {
                    'results': [
                        # latest_interaction is omitted, because the user does not have permission
                        # to view interactions
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                            },
                        },
                    ],
                },
                [CompanyPermission.view_company],
                id=(
                    'successful call to proxied API with company that can be hydrated '
                    'and user that has no interaction permissions'
                ),
            ),
            pytest.param(
                403,
                b'{"error":"msg"}',
                {'detail': 'You do not have permission to perform this action.'},
                [InteractionPermission.view_all],
                id='user missing view_company permission should get a 403',
            ),
            pytest.param(
                200,
                b'{"results":[{"duns_number":"7654321"}]}',
                {
                    'results': [
                        # latest_interaction is None, because the user does not have permission
                        # to view interactions
                        {
                            'dnb_company': {'duns_number': '7654321'},
                            'datahub_company': {
                                'id': '6083b732-b07a-42d6-ada4-c99999999999',
                                'latest_interaction': {
                                    'id': '6083b732-b07a-42d6-ada4-222222222222',
                                    'date': '2019-08-01',
                                    'created_on': '2019-08-01T16:00:00Z',
                                    'subject': 'Meeting with Joe Bloggs',
                                },
                            },
                        },
                    ],
                },
                [CompanyPermission.view_company, InteractionPermission.view_all],
                id=(
                    'user with both view_company and view_all_interaction permissions should get '
                    'a fully hydrated response'
                ),
            ),
        ),
    )
    def test_post_permissions(
        self,
        dnb_company_search_feature_flag,
        dnb_company_search_datahub_companies,
        requests_mock,
        response_status_code,
        upstream_response_content,
        response_data,
        permission_codenames,
    ):
        """
        Test for POST proxy.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=response_status_code,
            content=upstream_response_content,
        )
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:dnb-api:company-search')
        response = api_client.post(
            url,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert json.loads(response.content) == response_data
