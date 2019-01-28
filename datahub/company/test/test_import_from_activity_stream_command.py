from django.core.management import (
    call_command,
)


def test_command_exists_and_runs_without_error():
    """Tests that the import_from_activity_stream command exists and runs
    without error
    """
    call_command('import_from_activity_stream')
