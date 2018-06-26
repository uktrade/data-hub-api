from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException

from datahub.core.exceptions import DataHubException


class VirusScanException(DataHubException):
    """Exceptions raised when scanning documents for viruses."""


class DocumentDeleteException(DataHubException):
    """Exceptions raised when deletion of document failed."""


class TemporarilyUnavailableException(APIException):
    """Tell client that file is being scanned and is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _('File is being scanned for viruses, try again later.')
    default_code = 'file_is_being_scanned'
