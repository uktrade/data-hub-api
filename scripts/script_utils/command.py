from subprocess import CalledProcessError

from requests import HTTPError


class CommandError(Exception):
    """A fatal error when running a command."""


def print_error(exc):
    """Print an error that occurred when running a command."""
    messages = [f'ERROR: {exc}']

    if isinstance(exc, CalledProcessError) and exc.stderr:
        stderr = exc.stderr.decode(errors='replace')
        messages.append(f'Standard error: {stderr}')

    if isinstance(exc, HTTPError) and exc.response is not None:
        response_data = exc.response.json()
        messages.append(f'Response: {response_data}')

    print(*messages, sep='\n')  # noqa: T001
