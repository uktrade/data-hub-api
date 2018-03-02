from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class Conflict(APIException):
    """DRF Exception for the 409 status code."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Conflict with the current state of the resource.')
    default_code = 'conflict'
