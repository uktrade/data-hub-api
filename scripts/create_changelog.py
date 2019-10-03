#!/usr/bin/env python

"""
This is a script that does the following:

- takes a release type (major, minor or patch) as input and determines the new version number
- runs `git fetch`
- creates a local branch based on origin/develop
- generates a changelog for the release
- commits and pushes the changelog
- opens your web browser to the create PR page for the pushed branch

The script will abort if:

- there are uncommitted changes
- there are no news fragments on origin/develop
- the changelog branch for the new version already exists
- there are news fragments left behind after the changelog is generated
"""

import argparse
import glob
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote

from script_utils.current_version import get_current_version
from script_utils.version import Version

parser = argparse.ArgumentParser(description='Create and push a changelog for a new version.')
parser.add_argument('release_type', choices=Version._fields)


class CommandError(Exception):
    """A fatal error when running the script."""


def any_uncommitted_changes():
    """Checks if there are any uncommitted changes."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        check=True,
        capture_output=True,
    )
    return bool(result.stdout)


def local_branch_exists(branch):
    """Checks if a local branch exists."""
    try:
        subprocess.run(['git', 'show-ref', '--quiet', '--heads', '--', branch], check=True)
    except subprocess.CalledProcessError:
        return False

    return True


def remote_branch_exists(branch):
    """Checks if a remote branch exists."""
    try:
        subprocess.run(
            ['git', 'ls-remote', '--quiet', '--exit-code', 'origin', branch],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False

    return True


def list_news_fragments():
    """Return a list of files that are probable news fragments."""
    path = Path(__file__)
    root_path = path.resolve().parents[1]
    excluded_files = {'.gitignore', '_template.md.jinja2', 'README.md'}
    changelog_files = glob.iglob(f'{root_path}/changelog/**/*')
    return set(changelog_files) - excluded_files


def create_changelog(release_type):
    """Create and push a changelog."""
    current_version = get_current_version()

    if not current_version:
        raise CommandError('Failed to extract the current version number from the changelog.')

    new_version = current_version.increment_component(release_type)

    remote = 'origin'
    branch = f'changelog/{new_version}'
    commit_message = f'Add changelog for version {new_version}'

    if any_uncommitted_changes():
        raise CommandError(
            'There are uncommitted changes. Please commit, stash or delete them and try again.',
        )

    if local_branch_exists(branch):
        raise CommandError(
            f'Branch {branch} already exists locally. Please delete it and try again.',
        )

    if remote_branch_exists(branch):
        raise CommandError(
            f'Branch {branch} already exists remotely. Please delete it on GitHub and try again.',
        )

    subprocess.run(['git', 'fetch'], check=True)
    subprocess.run(['git', 'checkout', f'{remote}/develop'], check=True, capture_output=True)

    if not list_news_fragments():
        raise CommandError('There are no news fragments.')

    subprocess.run(['git', 'checkout', '-b', branch, f'{remote}/develop'], check=True)
    subprocess.run(['towncrier', '--version', str(new_version), '--yes'], check=True)

    remaining_news_fragment_paths = list_news_fragments()
    if remaining_news_fragment_paths:
        joined_paths = '\n'.join(remaining_news_fragment_paths)

        raise CommandError(
            'These news fragments were left behind:\n\n'
            f'{joined_paths}\n\n'
            'They may be misnamed. Please investigate.',
        )

    subprocess.run(['git', 'commit', '-m', commit_message], check=True)
    subprocess.run(['git', 'push', '--set-upstream', remote, branch], check=True)

    escaped_branch_name = quote(branch)
    webbrowser.open(f'https://github.com/uktrade/data-hub-leeloo/pull/new/{escaped_branch_name}')

    return branch


def main():
    """Run the script using command-line arguments."""
    args = parser.parse_args()

    try:
        branch_name = create_changelog(args.release_type)
    except (CommandError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}')  # noqa: T001
        return

    print(  # noqa: T001
        f'Branch {branch_name} was created, pushed and opened in your web browser. If anything '
        f'is wrong, edit your local branch manually and use git push --force-with-lease.',
    )


if __name__ == '__main__':
    main()
