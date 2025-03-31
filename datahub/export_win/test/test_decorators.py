import unittest
from unittest.mock import Mock

from rest_framework.response import Response

from datahub.export_win.decorators import validate_script_and_html_tags


class TestValidateScriptAndHtmlTags(unittest.TestCase):

    def test_input_with_html_tags(self):
        """Test the decorator with input containing HTML/script tags."""
        @validate_script_and_html_tags
        def mock_view(self, request, *args, **kwargs):
            return {'status': 'success'}, 200

        request = Mock()
        request.data = {'key': '<script>alert("XSS");</script>'}

        response = mock_view(None, request)
        assert response.status_code == 400
        assert 'error' in response.data
        assert response.data['error'] == 'Input contains disallowed HTML or script tags or symbols'

    def test_input_without_html_tags(self):
        """Test the decorator with input without HTML/script tags."""
        @validate_script_and_html_tags
        def mock_view(self, request, *args, **kwargs):
            return Response({'status': 'success'}, status=200)
        request = Mock()
        request.data = {'key': 'Hello world!'}
        response = mock_view(None, request)
        assert response.status_code == 200
        assert response.data['status'] == 'success'
