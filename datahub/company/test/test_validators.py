import pytest
from django.core.exceptions import ValidationError

from datahub.company.validators import RelaxedURLValidator


def test_valid_url_without_scheme():
    """Test acceptance of URL without scheme."""
    validator = RelaxedURLValidator()

    try:
        validator('www.google.com')
    except Exception:
        pytest.fail('Should accept URL without scheme')


def test_valid_url_still_works():
    """Test acceptance of URL with scheme."""
    validator = RelaxedURLValidator()

    try:
        validator('http://www.google.com')
    except Exception:
        pytest.fail('Should accept URL with scheme')


def test_invalid_url():
    """Test invalid URL."""
    validator = RelaxedURLValidator()

    with pytest.raises(ValidationError):
        validator('invalid')
