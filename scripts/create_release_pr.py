#!/usr/bin/env python

"""
This is a script that:

- runs `git fetch`
- creates a branch release/<version> based on origin/develop
- pushes this branch
- opens your web browser to the create PR page for the pushed branch (with master as
the base branch)

The script will abort if:

- a tag for the current version already exists
- there are news fragments on origin/develop
- there are uncommitted changes
- the release branch for the current version already exists
"""

import argparse
import subprocess
import webbrowser
from urllib.parse import quote, urlencode

from script_utils.command import CommandError, print_error
from script_utils.git import (
    any_uncommitted_changes,
    local_branch_exists,
    remote_branch_exists,
    remote_tag_exists,
)
from script_utils.news_fragments import list_news_fragments
from script_utils.versioning import get_current_version

GITHUB_BASE_REPO_URL = 'https://github.com/uktrade/data-hub-api'
RELEASE_GUIDE_URL = (
    'https://github.com/uktrade/data-hub-api/blob/develop/docs/'
    'How%20to%20prepare%20a%20release.md'
)
PR_BODY_TEMPLATE = """This is the release PR for version {version}.

Refer to [How to prepare a release]({release_guide_url}) for further information and the next \
steps.
"""

# Currently no real arguments – just used for --help etc.
parser = argparse.ArgumentParser(
    description='Create and push a release branch for the current version.',
)


def create_release_branch():
    """Create and push a release branch."""
    remote = 'origin'

    if any_uncommitted_changes():
        raise CommandError(
            'There are uncommitted changes. Please commit, stash or delete them and try again.',
        )

    subprocess.run(['git', 'fetch'], check=True)
    subprocess.run(['git', 'checkout', f'{remote}/develop'], check=True, capture_output=True)

    version = get_current_version()

    branch = f'release/{version}'
    tag = f'v{version}'

    if remote_tag_exists(tag):
        raise CommandError(
            f'A remote tag {tag} currently exists. It looks like version {version} has '
            f'already been released.',
        )

    news_fragment_paths = list_news_fragments()
    if news_fragment_paths:
        joined_paths = '\n'.join(news_fragment_paths)

        raise CommandError(
            'These are news fragments on origin/develop:\n\n'
            f'{joined_paths}\n\n'
            'Is the changelog up to date?',
        )

    if local_branch_exists(branch):
        raise CommandError(
            f'Branch {branch} already exists locally. Please delete it and try again.',
        )

    if remote_branch_exists(branch):
        raise CommandError(
            f'Branch {branch} already exists remotely. Please delete it on GitHub and try again.',
        )

    subprocess.run(['git', 'checkout', '-b', branch, f'{remote}/develop'], check=True)
    subprocess.run(['git', 'push', '--set-upstream', remote, branch], check=True)

    params = {
        'expand': '1',
        'title': f'Release {version}',
        'body': PR_BODY_TEMPLATE.format(version=version, release_guide_url=RELEASE_GUIDE_URL),
    }
    encoded_params = urlencode(params)
    escaped_branch_name = quote(branch)
    webbrowser.open(
        f'{GITHUB_BASE_REPO_URL}/compare/master...{escaped_branch_name}?{encoded_params}',
    )

    return branch


def main():
    """Run the script from the command line."""
    parser.parse_args()

    try:
        branch_name = create_release_branch()
    except (CommandError, subprocess.CalledProcessError) as exc:
        print_error(exc)
        return

    print(  # noqa: T001
        f'Branch {branch_name} was created, pushed and opened in your web browser.',
    )


if __name__ == '__main__':
    main()
