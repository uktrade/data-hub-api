from rest_framework.exceptions import ValidationError


class RepoDataValidationError(ValidationError):
    """Validation errors coming from the schema class."""

    pass
