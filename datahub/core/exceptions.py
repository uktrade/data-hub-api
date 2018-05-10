from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class DataHubException(Exception):
    """Base class for Data Hub exceptions (primarily used in thread pool tasks)."""


class APIConflictException(APIException):
    """DRF Exception for the 409 status code."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict with the current state of the resource.')
    default_code = 'conflict'


class APIBadRequestException(APIException):
    """DRF Exception for the 409 status code."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Cannot process request due to a client error.')
    default_code = 'bad_request'
