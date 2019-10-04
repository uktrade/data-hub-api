import subprocess


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
