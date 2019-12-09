import builtins
import io
from unittest.mock import Mock

import pytest

from script_utils.versioning import get_current_version, get_next_version, ReleaseType


FAKE_CHANGELOG_CONTENT = """# Data Hub API 15.2.0 (2019-09-26)

## Removals
"""


@pytest.mark.parametrize(
    'changelog_content,expected_version',
    [
        (FAKE_CHANGELOG_CONTENT, '15.2.0'),
        ('', None),
    ],
)
def test_get_current_version(changelog_content, expected_version, monkeypatch):
    """Test that get_current_version() parses and returns the latest version number."""
    # As we're patching open(), keep the patch active for as short as possible to avoid
    # unintended side effects
    with monkeypatch.context() as patch_context:
        patch_context.setattr(builtins, 'open', Mock(return_value=io.StringIO(changelog_content)))
        actual_version = get_current_version()

    assert actual_version == expected_version


@pytest.mark.parametrize(
    'starting_version,component_to_increment,incremented_version',
    [
        ('1.2.3', ReleaseType.patch, '1.2.4'),
        ('1.2.3', ReleaseType.minor, '1.3.0'),
        ('1.2.3', ReleaseType.major, '2.0.0'),
    ],
)
def test_get_next_version(starting_version, component_to_increment, incremented_version):
    """Test that the version is incremented as expected."""
    assert get_next_version(starting_version, component_to_increment) == incremented_version
