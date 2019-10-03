import pytest

from script_utils.version import Version


@pytest.mark.parametrize(
    'starting_version,increment_component,incremented_version',
    [
        (Version(1, 2, 3), 'patch', Version(1, 2, 4)),
        (Version(1, 2, 3), 'minor', Version(1, 3, 0)),
        (Version(1, 2, 3), 'major', Version(2, 0, 0)),
    ],
)
def test_increment_version(starting_version, increment_component, incremented_version):
    """Test that the version is incremented as expected."""
    assert starting_version.increment_component(increment_component) == incremented_version
