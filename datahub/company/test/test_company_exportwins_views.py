import uuid

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.merge import merge_companies
from datahub.company.models import CompanyPermission
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    HawkMockJSONResponse,
)


class TestGetCompanyExportWins(APITestMixin):
    """Test for GET endpoints that return export wins related to a company."""

    def test_returns_401_if_unauthenticated(self, api_client):
        """Test that a 401 is returned if the user is unauthenticated."""
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        'permission_codenames,expected_status',
        (
            ([], status.HTTP_403_FORBIDDEN),
            (['view_company'], status.HTTP_403_FORBIDDEN),
        ),
    )
    def test_permission_checking(self, permission_codenames, expected_status):
        """Test that a 403 is returned if the user has not enough permissions."""
        user = create_test_user(permission_codenames=permission_codenames)
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        'match_response',
        [
            pytest.param(
                {},
            ),
            pytest.param(
                {
                    'matches': [],
                },
            ),
            pytest.param(
                {
                    'matches': [
                        {
                            'id': 1,
                            'similarity': '100000',
                        },
                    ],
                },
            ),
            pytest.param(
                {
                    'matches': [
                        {
                            'id': 1,
                            'match_id': None,
                            'similarity': '100000',
                        },
                    ],
                },
            ),
        ],
    )
    def test_no_match_id_404_conditions(
        self,
        requests_mock,
        match_response,
    ):
        """Test that any issues with company matching service results in a 200 empty list."""
        company_dynamic_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
            response=match_response,
        )
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=status.HTTP_200_OK,
            text=company_dynamic_response,
        )

        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_408_REQUEST_TIMEOUT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_company_matching_upstream_error_conditions(self, requests_mock, response_status):
        """Test company matching service error conditions."""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=response_status,
        )
        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def _get_matching_service_response(self, match_ids):
        company_matching_reponse = {
            'matches': [
                {
                    'id': 1,
                    'match_id': match_id,
                    'similarity': '100000',
                }
                for match_id in match_ids
            ],
        }
        company_dynamic_response = HawkMockJSONResponse(
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
            response=company_matching_reponse,
        )
        return company_dynamic_response

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_408_REQUEST_TIMEOUT,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_export_wins_upstream_error_conditions(self, requests_mock, response_status):
        """Test export wins service error conditions."""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=200,
            text=self._get_matching_service_response([1]),
        )

        requests_mock.get(
            '/wins/match?match_id=1',
            status_code=response_status,
        )

        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_502_BAD_GATEWAY

    def test_no_company_with_pk_raises_404(self):
        """
        Test if company pk provided in get parameters doesn't match,
        404 is raised.
        """
        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        dummy_company_id = uuid.uuid4()
        url = reverse('api-v4:company:export-win', kwargs={'pk': dummy_company_id})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_get_export_wins_success(
        self,
        requests_mock,
    ):
        """Test get wins in a successful scenario."""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=200,
            text=self._get_matching_service_response([1]),
        )

        export_wins_response = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515521',
                    'date': '2016-05-25',
                    'created': '2020-02-18T15:36:02.782000Z',
                    'country': 'CA',
                    'sector': 251,
                    'business_potential': 1,
                    'business_type': '',
                    'name_of_export': '',
                    'officer': {
                        'name': 'lead officer name',
                        'email': '',
                        'team': {
                            'type': 'tcp',
                            'sub_type': 'tcp:12',
                        },
                    },
                    'contact': {
                        'name': 'customer name',
                        'email': 'noname@somecompany.com',
                        'job_title': 'customer job title',
                    },
                    'value': {
                        'export': {
                            'value': 100000,
                            'breakdowns': [],
                        },
                    },
                    'customer': 'Some Company Limited',
                    'response': None,
                    'hvc': {
                        'code': 'E24116',
                        'name': 'AER-01',
                    },
                },
            ],
        }
        export_wins_dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response=export_wins_response,
        )
        requests_mock.get(
            '/wins/match?match_id=1',
            status_code=200,
            text=export_wins_dynamic_response,
        )

        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        api_client = self.create_api_client(user=user)
        company = CompanyFactory()
        url = reverse('api-v4:company:export-win', kwargs={'pk': company.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json() == export_wins_response

    def test_get_export_wins_one_merged_company_success(
        self,
        requests_mock,
    ):
        """Test get wins for both source and target, when a company was merged."""
        source_company = CompanyFactory()
        target_company = CompanyFactory()
        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        merge_companies(source_company, target_company, user)

        requests_mock.register_uri(
            'POST',
            '/api/v1/company/match/',
            [
                {'text': self._get_matching_service_response([1, 2]), 'status_code': 200},
            ],
        )

        export_wins_response = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515521',
                    'date': '2016-05-25',
                    'created': '2020-02-18T15:36:02.782000Z',
                    'country': 'CA',
                },
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515234',
                    'date': '2016-07-25',
                    'created': '2020-04-18T15:36:02.782000Z',
                    'country': 'US',
                },
            ],
        }
        export_wins_dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response=export_wins_response,
        )
        requests_mock.get(
            '/wins/match?match_id=1,2',
            status_code=200,
            text=export_wins_dynamic_response,
        )

        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:export-win', kwargs={'pk': target_company.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json() == export_wins_response

    def test_get_export_wins_multiple_merged_companies_success(
        self,
        requests_mock,
    ):
        """
        Test get wins for all source companies and target,
        when a company was merged.
        """
        source_company_1 = CompanyFactory()
        target_company = CompanyFactory()
        user = create_test_user(
            permission_codenames=(
                CompanyPermission.view_export_win,
            ),
        )
        merge_companies(source_company_1, target_company, user)

        source_company_2 = CompanyFactory()
        merge_companies(source_company_2, target_company, user)

        requests_mock.register_uri(
            'POST',
            '/api/v1/company/match/',
            [
                {'text': self._get_matching_service_response([1, 2, 3]), 'status_code': 200},
            ],
        )

        export_wins_response = {
            'count': 3,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515521',
                    'date': '2016-05-25',
                    'created': '2020-02-18T15:36:02.782000Z',
                    'country': 'CA',
                },
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515234',
                    'date': '2016-07-25',
                    'created': '2020-04-18T15:36:02.782000Z',
                    'country': 'US',
                },
                {
                    'id': 'e3013078-7b3e-4359-83d9-cd003a515456',
                    'date': '2016-09-25',
                    'created': '2020-12-18T15:36:02.782000Z',
                    'country': 'BL',
                },
            ],
        }
        export_wins_dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response=export_wins_response,
        )
        requests_mock.get(
            '/wins/match?match_id=1,2,3',
            status_code=200,
            text=export_wins_dynamic_response,
        )

        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:export-win', kwargs={'pk': target_company.id})
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.json() == export_wins_response
