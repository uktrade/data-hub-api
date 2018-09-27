from django.http.multipartparser import parse_header
from oauth2_provider.oauth2_backends import OAuthLibCore
from rest_framework import HTTP_HEADER_ENCODING


class ContentTypeAwareOAuthLibCore(OAuthLibCore):
    """Extends the default OAuthLibCore to limit the use of request body."""

    def extract_body(self, request):
        """
        Returns POST contents if content type is application/x-www-form-urlencoded.

        Refer to https://tools.ietf.org/html/rfc6750#section-2.2 for more information.
        """
        content_type = request.content_type
        base_media_type, _ = parse_header(content_type.encode(HTTP_HEADER_ENCODING))
        if base_media_type == 'application/x-www-form-urlencoded':
            return request.POST.items()
        return ()
