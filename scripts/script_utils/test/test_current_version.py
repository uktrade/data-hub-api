import builtins
import io
from unittest.mock import Mock

import pytest

from script_utils.current_version import get_current_version
from script_utils.version import Version


FAKE_CHANGELOG_CONTENT = """# Data Hub API 15.2.0 (2019-09-26)

## Removals
"""


@pytest.mark.parametrize(
    'changelog_content,expected_version',
    [
        (FAKE_CHANGELOG_CONTENT, Version(15, 2, 0)),
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
