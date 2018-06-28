from unittest.mock import Mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.core.validators.not_archived import NotArchivedValidator


def test_fails_validation_if_archived():
    """Test that an object fails validation if it is archived."""
    serializer = Mock(instance=Mock(archived=True))
    validator = NotArchivedValidator()
    validator.set_context(serializer)
    with pytest.raises(ValidationError) as excinfo:
        validator({})

    assert excinfo.value.detail == ['This record has been archived and cannot be edited.']


def test_passes_validation_if_not_archived():
    """Test that an object passes validation if it is archived."""
    serializer = Mock(instance=Mock(archived=False))
    validator = NotArchivedValidator()
    validator.set_context(serializer)
    try:
        validator({})
    except ValidationError:
        pytest.xfail('Should not raise a ValidationError.')
