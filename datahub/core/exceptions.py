from rest_framework.views import exception_handler
from rest_framework_json_api import exceptions as json_api_exceptions


def versioned_exception_handler(exc, context):
    """Version based exception handler."""
    if getattr(context['request'], 'version', None) == 'v2':
        return json_api_exceptions.exception_handler(exc, context)
    return exception_handler(exc, context)
