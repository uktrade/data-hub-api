from django.utils.translation import gettext_lazy as _
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
    """DRF Exception for the 400 status code."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Cannot process request due to a client error.')
    default_code = 'bad_request'


class APIMethodNotAllowedException(APIException):
    """DRF Exception for the 405 status code."""

    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _('Method is not allowed.')
    default_code = 'method_not_allowed'


class APIUpstreamException(APIException):
    """DRF Exception for the 502 status code."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = _('Cannot process request due to an error in an upstream service.')
    default_code = 'bad_gateway'


class SimulationRollback(Exception):
    """Used to roll back deletions during a simulation."""
