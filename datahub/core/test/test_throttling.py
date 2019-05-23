import time

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from datahub.core.throttling import PathRateThrottle


class Path3SecRateThrottle(PathRateThrottle):
    """PathRateThrottle with a specific rate."""

    scope = 'path'
    rate = '3/sec'

    def __init__(self, *args, **kwargs):
        """
        Re-define self.timer to allow classes to mock time.time if needed.
        This is because DRF sets this property on the class and it doesn't give
        opportunities for tests to override it.
        """
        super(Path3SecRateThrottle, self).__init__(*args, **kwargs)
        self.timer = time.time


class MockView(APIView):
    """Simple APIView to test PathRateThrottle."""

    authentication_classes = ()
    permission_classes = ()
    throttle_classes = (Path3SecRateThrottle,)

    def get(self, request):
        """Simple implementatin of the GET method."""
        return Response('foo')


@pytest.mark.usefixtures('local_memory_cache')
class TestPathRateThrottle:
    """Tests for the PathRateThrottle class."""

    @freeze_time('2018-03-01 00:00:00')
    def test_requests_are_throttled(self):
        """Test that the requests are throttled."""
        factory = APIRequestFactory()

        for _ in range(4):
            request = factory.get('/some-path/')
            response = MockView.as_view()(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @freeze_time('2018-03-01 00:00:00')
    def test_query_params_do_not_count(self):
        """
        Test that query params are ignored.
        Eg. GET /some-path/ and GET /some-path/?param=value
        are treated as the same.
        """
        factory = APIRequestFactory()

        for index in range(4):
            request = factory.get(f'/some-path/?param={index}')
            response = MockView.as_view()(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @freeze_time('2018-03-01 00:00:00')
    def test_case_does_not_count(self):
        """
        Test that the match is case insensitive..
        Eg. GET /some-path/ and GET /some-Path/
        are treated as the same.
        """
        factory = APIRequestFactory()

        for path in ['path', 'Path', 'pAth', 'paTh']:
            request = factory.get(f'/some-{path}/')
            response = MockView.as_view()(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @freeze_time('2018-03-01 00:00:00')
    def test_throttling_is_per_path(self):
        """
        Test that throttling is per path.
        Eg. GET /some-path-1/ and POST /some-path-2/
        are not treated as the same.
        """
        factory = APIRequestFactory()

        for _ in range(4):
            request = factory.get('/some-path/')
            response = MockView.as_view()(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        request = factory.get('/some-path2/')
        response = MockView.as_view()(request)
        assert response.status_code == status.HTTP_200_OK
