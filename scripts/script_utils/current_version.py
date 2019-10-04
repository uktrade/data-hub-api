import re
from pathlib import PurePath

from script_utils.version import Version


CHANGELOG_PATH = PurePath(__file__).parents[2] / 'CHANGELOG.md'


def get_current_version():
    """
    Gets the current version number from the changelog.

    Note: In future we may want to write and obtain the version number to and from a more
    authoritative source e.g. a module in the datahub package.
    """
    with open(CHANGELOG_PATH, 'r') as file:
        changelog = file.read(10_000)

    match = re.search(r' (?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+) ', changelog)

    if match:
        return Version.from_dict(match.groupdict())

    return None
