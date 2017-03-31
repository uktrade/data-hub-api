from rest_framework.exceptions import ValidationError


class RepoDataValidation(ValidationError):
    """Validation errors coming from the schema class."""

    pass
