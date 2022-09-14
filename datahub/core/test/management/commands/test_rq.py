import logging
from unittest import mock

from django.core.management import call_command


class PickleableMock:
    called = False
    times = 0

    @staticmethod
    def reset():
        PickleableMock.called = False
        PickleableMock.times = 0

    @staticmethod
    def handler():
        PickleableMock.called = True
        PickleableMock.times += 1


def test_rq_health_check_is_called_for_all_queues_setup(monkeypatch):
    mock = PickleableMock()
    monkeypatch.setattr(
        'datahub.core.queues.health_check.queue_health_check',
        mock.handler,
    )

    call_command('test_rq')

    assert mock.called is True
    assert mock.times == 3


def test_rq_runs_logger_to_sentry(monkeypatch):
    logger = logging.getLogger('datahub.core.queues.health_check')
    with mock.patch.object(logger, 'info') as mock_info:
        call_command('test_rq')

        assert mock_info.assert_called


def test_rq_writes_a_log_file_when_in_debug(monkeypatch):
    log_health_mock = mock.Mock
    monkeypatch.setenv('DEBUG', True)
    monkeypatch.setattr(
        'datahub.core.queues.health_check.log_health',
        log_health_mock,
    )

    call_command('test_rq')

    assert log_health_mock.called
