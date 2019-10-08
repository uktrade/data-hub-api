import subprocess
from enum import Enum


def any_uncommitted_changes():
    """Check if there are any uncommitted changes."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        check=True,
        capture_output=True,
    )
    return bool(result.stdout)


def local_branch_exists(branch):
    """Check if a local branch exists."""
    try:
        subprocess.run(['git', 'show-ref', '--quiet', '--heads', '--', branch], check=True)
    except subprocess.CalledProcessError:
        return False

    return True


def remote_branch_exists(branch):
    """Check if a remote branch exists."""
    return _remote_ref_exists(branch, _RefTypeArg.head)


def remote_tag_exists(tag):
    """Check if a remote tag exists."""
    return _remote_ref_exists(tag, _RefTypeArg.tag)


class _RefTypeArg(Enum):
    head = '--heads'
    tag = '--tags'


def _remote_ref_exists(ref, ref_type_arg):
    """Checks if a remote reference exists."""
    try:
        subprocess.run(
            ['git', 'ls-remote', '--quiet', '--exit-code', ref_type_arg.value, 'origin', ref],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False

    return True
