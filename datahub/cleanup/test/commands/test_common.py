import pytest
from django.core import management
from django.core.management import CommandError

from datahub.cleanup.management.commands import delete_old_records, delete_orphans

COMMAND_CLASSES = [
    delete_old_records.Command,
    delete_orphans.Command,
]


@pytest.mark.parametrize('cleanup_command_cls', COMMAND_CLASSES, ids=str)
def test_fails_with_invalid_model(cleanup_command_cls):
    """Test that if an invalid value for model is passed in, the command errors."""
    with pytest.raises(CommandError):
        management.call_command(cleanup_command_cls(), 'invalid')
