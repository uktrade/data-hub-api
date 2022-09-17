from unittest.mock import call, MagicMock

import pytest

from django.core.management import call_command, CommandError

from datahub.core.management.commands import purge_queue


@pytest.mark.django_db
class TestPurgeQueueCommandShould:

    def test_fail_when_no_arguments_assigned(self):
        command = purge_queue.Command()

        with pytest.raises(CommandError) as excinfo:
            call_command(command)

        assert str(excinfo.value) == 'Error: the following arguments are required: queue_name'

    def test_fail_when_unsupported_name_assigned(self):
        command = purge_queue.Command()

        with pytest.raises(CommandError) as excinfo:
            call_command(command, 'invalid-queue')

        assert str(excinfo.value) == (
            "Error: argument queue_name: invalid choice: 'invalid-queue' "
            "(choose from 'long-running', 'short-running', 'test-rq-health')"
        )

    def test_fail_when_unsupported_queue_state_assigned(self):
        command = purge_queue.Command()

        with pytest.raises(CommandError) as excinfo:
            call_command(command, 'long-running', '--queue_state=finished')

        assert str(excinfo.value) == (
            "Error: argument --queue_state: invalid choice: 'finished' "
            "(choose from 'queued', 'failed')"
        )

    def test_purging_queued_queues_succeeds(self, monkeypatch):
        mock_scheduler = MagicMock()
        monkeypatch.setattr(
            'datahub.core.management.commands.purge_queue.DataHubScheduler',
            mock_scheduler,
        )

        command = purge_queue.Command()

        success_message = call_command(command, 'test-rq-health', '--queue_state=queued')

        assert success_message == 'Successfully purged queued on test-rq-health queue'
        assert call().__enter__().purge('test-rq-health', 'queued') in (
            mock_scheduler.mock_calls
        )

    def test_purging_failed_queues_succeeds(self, monkeypatch):
        mock_scheduler = MagicMock()
        monkeypatch.setattr(
            'datahub.core.management.commands.purge_queue.DataHubScheduler',
            mock_scheduler,
        )

        command = purge_queue.Command()

        success_message = call_command(command, 'long-running', '--queue_state=failed')
        assert success_message == 'Successfully purged failed on long-running queue'
        assert call().__enter__().purge('long-running', 'failed') in (
            mock_scheduler.mock_calls
        )
