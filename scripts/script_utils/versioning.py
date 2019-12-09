import re
from enum import Enum
from pathlib import PurePath

from semantic_version import Version


CHANGELOG_PATH = PurePath(__file__).parents[2] / 'CHANGELOG.md'


class ReleaseType(Enum):
    """Release types."""

    major = 'major'
    minor = 'minor'
    patch = 'patch'


def get_current_version():
    """
    Get the current version number from the changelog.

    Note: In future we may want to write and obtain the version number to and from a more
    authoritative source e.g. a module in the datahub package.
    """
    with open(CHANGELOG_PATH, 'r') as file:
        changelog = file.read(10_000)

    match = re.search(r' (?P<version>\d+\.\d+\.\d+) ', changelog)

    if match:
        return match.group('version')

    return None


def get_next_version(current_version, release_type):
    """Increment a version for a particular release type."""
    if not isinstance(release_type, ReleaseType):
        raise TypeError()

    parsed_version = Version(current_version)

    if release_type is ReleaseType.major:
        return str(parsed_version.next_major())

    if release_type is ReleaseType.minor:
        return str(parsed_version.next_minor())

    return str(parsed_version.next_patch())
