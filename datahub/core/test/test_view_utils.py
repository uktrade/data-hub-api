from unittest.mock import Mock

import pytest

from datahub.core.view_utils import enforce_request_content_type


class TestViewUtils:
    """
    Tests view_utils module.
    """

    @pytest.mark.parametrize(
        'enforced_content_type,content_type,passes',
        (
            ('application/json', 'application/json', True),
            ('application/json', 'application/j', False),
            ('application/json', None, False),
            ('application/json', 'text/html', False),
            ('application/json', 'text/javascript', False),
            ('application/json', 'application/ld+json', False),
            ('application/json', 'application/json; charset=utf-8', True),
        ),
    )
    def test_enforce_request_content_type(self, enforced_content_type, content_type, passes):
        """
        Test enforce_request_content_type decorator.
        """
        mocked_request = Mock()
        mocked_request.content_type = content_type

        @enforce_request_content_type(enforced_content_type)
        def view_method(self, request):
            return 'foobar'

        result = view_method(None, mocked_request)
        if passes:
            assert result == 'foobar'
        else:
            assert result.status_code == 406
