from enum import Enum
from pathlib import PurePath

from semantic_version import Version


DATA_HUB_PACKAGE_PATH = PurePath(__file__).parents[2]
VERSION_FILE_PATH = DATA_HUB_PACKAGE_PATH / 'datahub' / 'VERSION'


class ReleaseType(Enum):
    """Release types."""

    major = 'major'
    minor = 'minor'
    patch = 'patch'


def get_current_version():
    """Get the current version number from the package."""
    with open(VERSION_FILE_PATH, 'r') as version_file:
        return version_file.read().strip()


def set_current_version(new_version):
    """Write the current version number to the package."""
    with open(VERSION_FILE_PATH, 'w') as version_file:
        version_file.write(f'{new_version}\n')


def get_next_version(release_type):
    """Increment a version for a particular release type."""
    if not isinstance(release_type, ReleaseType):
        raise TypeError()

    version = Version(get_current_version())

    if release_type is ReleaseType.major:
        return str(version.next_major())

    if release_type is ReleaseType.minor:
        return str(version.next_minor())

    return str(version.next_patch())
