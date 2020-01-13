from subprocess import CalledProcessError
from unittest.mock import Mock

import pytest
from requests import HTTPError

from script_utils.command import CommandError, print_error


@pytest.mark.parametrize(
    'exc,expected_output',
    [
        (
            CommandError('Test error'),
            'ERROR: Test error\n',
        ),
        (
            CalledProcessError(1, 'some-command'),
            """ERROR: Command 'some-command' returned non-zero exit status 1.\n""",
        ),
        (
            CalledProcessError(1, 'some-command', stderr=b'some error'),
            """ERROR: Command 'some-command' returned non-zero exit status 1.
Standard error: some error
""",
        ),
        (
            HTTPError('some error'),
            'ERROR: some error\n',
        ),
        (
            HTTPError(
                'some error',
                response=Mock(
                    json=Mock(return_value={'error': 'message'}),
                    # If the status code is an error code, Response.__bool__() will return False
                    __bool__=Mock(return_value=False),
                ),
            ),
            """ERROR: some error
Response: {'error': 'message'}
""",
        ),
    ],
)
def test_print_error(exc, expected_output, capsys):
    """Test that print_error() prints the expected message for various exceptions."""
    print_error(exc)

    stdout, _ = capsys.readouterr()
    assert expected_output == stdout
