from django.http import HttpResponse
from django.http.multipartparser import parse_header
from rest_framework import HTTP_HEADER_ENCODING, status


def enforce_request_content_type(content_type):
    """
    Decorator to enforce request content types to be a certain value.  Returns
    a 406 HttpResponse if the value is not allowed.

    This should be used on rest framework view methods which have `request` as
    the first argument
    """
    def _enforce_request_content_type(f):
        def wrapper(self, *args, **kwargs):
            request = args[0]
            content_type = request.content_type or ''
            # check that the content type of the request is json
            base_media_type, _ = parse_header(content_type.encode(HTTP_HEADER_ENCODING))
            if base_media_type != 'application/json':
                return HttpResponse(
                    'Please set Content-Type header value to application/json',
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )
            return f(self, *args, **kwargs)
        return wrapper
    return _enforce_request_content_type
