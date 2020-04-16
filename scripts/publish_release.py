#!/usr/bin/env python

"""
This is a script that:

- runs `git fetch`
- gets the version number from origin/master
- extracts the changelog for that version from CHANGELOG.md
- creates a release on GitHub for that version
- prints the URL for the created release

The script will abort if:

- a tag for the current version already exists

(This script works without checking out a different branch, as it does not have to commit
anything.)

A GitHub access token with the public_repo scope is required.
"""

import argparse
import os
import subprocess
import sys
from getpass import getpass

import requests
from requests import HTTPError

from script_utils.changelog import extract_version_changelog
from script_utils.command import CommandError, print_error
from script_utils.git import get_file_contents, remote_tag_exists

GITHUB_RELEASE_API_URL = 'https://api.github.com/repos/uktrade/data-hub-api/releases'


# Currently no real arguments – just used for --help etc.
parser = argparse.ArgumentParser(
    description="""Publishes the current release on GitHub.

A GitHub access token with the public_repo scope is required. The token can be provided
using the GITHUB_TOKEN environment variable. If that variable is not set, you will be prompted
for a token.
""",
)


def publish_release():
    """Publish the release on GitHub."""
    remote = 'origin'
    branch = 'master'

    subprocess.run(['git', 'fetch'], check=True)

    version = get_file_contents(f'{remote}/{branch}', 'datahub/VERSION').strip()
    tag = f'v{version}'

    if remote_tag_exists(tag):
        raise CommandError(
            f'A remote tag {tag} currently exists. It looks like this release has already been'
            f' published.',
        )

    changelog = get_file_contents(f'{remote}/{branch}', 'CHANGELOG.md')
    version_changelog = extract_version_changelog(changelog, version)

    if not version_changelog:
        raise CommandError(f'Failed to extract the changelog for version {version}.')

    token = os.environ.get('GITHUB_TOKEN') or getpass('GitHub access token: ')

    response = requests.post(
        GITHUB_RELEASE_API_URL,
        headers={
            'Authorization': f'Bearer {token}',
        },
        json={
            'tag_name': tag,
            'target_commitish': 'master',
            'name': tag,
            'body': version_changelog,
        },
    )
    response.raise_for_status()
    response_data = response.json()

    return tag, response_data['html_url']


def main():
    """Run the script using command-line arguments."""
    parser.parse_args()

    try:
        tag, url = publish_release()
    except (CommandError, HTTPError, subprocess.CalledProcessError) as exc:
        print_error(exc)
        sys.exit(1)

    msg = f"""Release {tag} was published at:
{url}.

If anything is wrong, edit the release on GitHub.
"""
    print(msg)  # noqa: T001


if __name__ == '__main__':
    main()
