from pathlib import PurePath

import pytest

from datahub.company.test.factories import CompanyFactory
from datahub.core.management.commands.loadinitialmetadata import (
    _ensure_no_existing_data, ExistingDataFoundError,
)

pytestmark = pytest.mark.django_db


def test_ensure_no_existing_data_fails_when_existing_data():
    """Checks that an error is raised when data already exists in the database."""
    CompanyFactory()
    fixture_path = PurePath(__file__).parent / 'loadinitialmetadata_test_data.yaml'
    with pytest.raises(ExistingDataFoundError):
        _ensure_no_existing_data([fixture_path])


def test_ensure_no_existing_data_does_not_fail_when_no_existing_data():
    """Checks that no error is raised when data doesn't currently exist in the database."""
    fixture_path = PurePath(__file__).parent / 'loadinitialmetadata_test_data.yaml'
    assert _ensure_no_existing_data([fixture_path]) is None
