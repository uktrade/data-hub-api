import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.activity_feed.views import ActivityFeedView
from datahub.core.test_utils import APITestMixin, create_test_user


def pytest_generate_tests(metafunc):
    """
    Parametrizes the tests that use the `insufficient_activity_permissions` fixture
    by creating lists with all required permissions except one.
    """
    if 'insufficient_activity_permissions' in metafunc.fixturenames:
        perms = ActivityFeedView.ACTIVITY_MODELS_PERMISSIONS_REQUIRED
        insufficient_activity_permissions = [
            pytest.param(
                [
                    perm
                    for perm in perms
                    if perm != perm_to_exclude
                ],
                id=f'without {perm_to_exclude}',
            )
            for perm_to_exclude in perms
        ]
        metafunc.parametrize(
            'insufficient_activity_permissions',
            insufficient_activity_permissions,
        )


class TestActivityFeedView(APITestMixin):
    """Activity Feed view test case."""

    @pytest.mark.parametrize(
        'request_data,response_status_code,response_content',
        (
            (
                b'{"arg": "value"}',
                200,
                b'{"took":27}',
            ),
            (
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
            ),
            (
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
            ),
        ),
    )
    def test_get(self, requests_mock, request_data, response_status_code, response_content):
        """Test for GET proxy."""
        requests_mock.get(
            settings.ACTIVITY_STREAM_OUTGOING_URL,
            status_code=response_status_code,
            content=response_content,

        )

        url = reverse('api-v4:activity-feed:index')
        # api_client.get transforms data into querystring hence generic is used here
        response = self.api_client.generic(
            'GET',
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert response.content == response_content
        assert requests_mock.last_request.body == request_data

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
            ('application/json', status.HTTP_200_OK),
        ),
    )
    def test_content_type(self, requests_mock, content_type, expected_status_code):
        """Test that 406 is returned if Content Type is not application/json."""
        requests_mock.get(
            settings.ACTIVITY_STREAM_OUTGOING_URL,
            status_code=status.HTTP_200_OK,
        )

        url = reverse('api-v4:activity-feed:index')
        response = self.api_client.get(
            url,
            content_type=content_type,
        )

        assert response.status_code == expected_status_code

    def test_returns_empty_list_without_all_required_perms(
        self,
        insufficient_activity_permissions,
    ):
        """
        Test that an empty list is returned if the authenticated user doesn't have permission
        to view all activity models.
        """
        requester = create_test_user(
            permission_codenames=(
                perm.rsplit('.', maxsplit=1)[1]  # get only the codename
                for perm in insufficient_activity_permissions
            ),
        )

        url = reverse('api-v4:activity-feed:index')
        api_client = self.create_api_client(user=requester)
        response = api_client.generic(
            'GET',
            url,
            data={},
            content_type='application/json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'hits': {
                'total': 0,
                'hits': [],
            },
        }
