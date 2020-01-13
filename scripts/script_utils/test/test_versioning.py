import builtins
from io import StringIO
from unittest.mock import call, MagicMock, Mock

import pytest

from script_utils.versioning import (
    get_current_version,
    get_next_version,
    ReleaseType,
    set_current_version,
)


def test_get_current_version(monkeypatch):
    """Test that get_current_version() returns the current version number."""
    fake_version = '1.2.3'

    # As we're patching open(), keep the patch active for as short as possible to avoid
    # unintended side effects
    with monkeypatch.context() as patch_context:
        file_mock = Mock(return_value=StringIO(f'{fake_version}\n'))
        patch_context.setattr(builtins, 'open', file_mock)

        assert get_current_version() == fake_version


def test_set_current_version(monkeypatch):
    """Test that set_current_version() writes out the new version number."""
    fake_version = '1.2.3'

    # As we're patching open(), keep the patch active for as short as possible to avoid
    # unintended side effects
    with monkeypatch.context() as patch_context:
        file_mock = MagicMock()
        patch_context.setattr(builtins, 'open', file_mock)

        set_current_version(fake_version)

    write_mock = file_mock.return_value.__enter__.return_value.write
    assert write_mock.call_args == call(f'{fake_version}\n')


@pytest.mark.parametrize(
    'starting_version,component_to_increment,incremented_version',
    [
        ('1.2.3', ReleaseType.patch, '1.2.4'),
        ('1.2.3', ReleaseType.minor, '1.3.0'),
        ('1.2.3', ReleaseType.major, '2.0.0'),
    ],
)
def test_get_next_version(
    starting_version,
    component_to_increment,
    incremented_version,
    monkeypatch,
):
    """Test that the version is incremented as expected."""
    monkeypatch.setattr(
        'script_utils.versioning.get_current_version',
        Mock(return_value=starting_version),
    )
    assert get_next_version(component_to_increment) == incremented_version
