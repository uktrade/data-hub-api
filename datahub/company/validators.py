"""Custom validators."""
from django.core.validators import URLValidator


class RelaxedURLValidator(URLValidator):
    """Url validator that accepts URL without scheme."""

    def __call__(self, value):
        """Allow missing scheme in URL."""
        if '://' not in value:
            value = 'http://' + value

        super().__call__(value)
