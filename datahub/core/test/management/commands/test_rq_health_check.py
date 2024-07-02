import logging
from unittest import mock
from unittest.mock import patch

import pytest

from django.core.management import call_command


class MockWorker:
    """
    Mock queue names object returned by worker
    """

    queue_name = ''

    def __init__(self, queue_name, *args, **kwargs):
        self.queue_name = queue_name

    def queue_names(self):
        return self.queue_name


def test_rq_health_check_ok():
    logger = logging.getLogger('datahub.core.management.commands.rq_health_check')
    with patch(
        'datahub.core.management.commands.rq_health_check.Worker.all',
        return_value=[MockWorker(['short-running']), MockWorker(['long-running'])],
    ):
        with mock.patch.object(logger, 'info') as mock_info:
            with pytest.raises(SystemExit) as exception_info:
                call_command('rq_health_check', '--queue=short-running')

            assert exception_info.value.code == 0
            assert 'OK' in str(mock_info.call_args_list)
            assert mock_info.call_count == 1


def test_rq_health_check_rq_not_running():
    logger = logging.getLogger('datahub.core.management.commands.rq_health_check')
    with patch(
        'datahub.core.management.commands.rq_health_check.Worker.all',
        return_value=[MockWorker(['long-running'])],
    ):
        with mock.patch.object(logger, 'error') as mock_error:
            with pytest.raises(SystemExit) as exception_info:
                call_command('rq_health_check', '--queue=short-running')

            assert exception_info.value.code == 1
            assert "RQ queue not running: {\'short-running\'}" in str(mock_error.call_args_list)
            assert mock_error.call_count == 1


def test_command_called_without_parameter():
    logger = logging.getLogger('datahub.core.management.commands.rq_health_check')
    with mock.patch.object(logger, 'error') as mock_error:
        with pytest.raises(SystemExit) as exception_info:
            call_command('rq_health_check')

        assert exception_info.value.code == 1
        assert 'Nothing checked! Please provide --queue parameter' \
            in str(mock_error.call_args_list)
        assert mock_error.call_count == 1
