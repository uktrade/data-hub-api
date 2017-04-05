from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError


class RepoDataValidationError(ValidationError):
    """Validation errors coming from the schema class."""

    pass


class Conflict(APIException):
    """Conflict exception."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflict.'
