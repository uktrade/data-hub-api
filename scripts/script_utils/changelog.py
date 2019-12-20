import re


def extract_version_changelog(changelog, version):
    """Extract the changelog for a particular version from the entire changelog."""
    escaped_version = re.escape(version)

    pattern = rf"""(?m:^)# Data Hub API {escaped_version} \([0-9-]+\)
(?P<content>.*?)
(# Data Hub API|$)"""

    match = re.search(pattern, changelog, flags=re.DOTALL)

    if match:
        return match.group('content').strip()

    return None
