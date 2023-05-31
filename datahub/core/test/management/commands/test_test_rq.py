import logging
from datetime import datetime
from unittest import mock

import pytest

from django.core.management import call_command

from datahub.core.queues.errors import RetryError
from datahub.core.queues.health_check import show_health_status_for_jobs
from datahub.core.test.queues.test_scheduler import PickleableMock


def test_rq_health_check_is_called_for_all_queues_setup(monkeypatch):
    mock = PickleableMock()
    monkeypatch.setattr(
        'datahub.core.queues.health_check.queue_health_check',
        mock.queue_handler,
    )

    call_command('test_rq', '--generated_jobs=2')

    assert mock.called is True
    assert mock.times == 5


def test_rq_runs_logger_to_sentry():
    logger = logging.getLogger('datahub.core.queues.health_check')
    with mock.patch.object(logger, 'info') as mock_info:
        call_command('test_rq', '--generated_jobs=10')

        assert mock_info.assert_called


def test_show_health_status_succeeds_when_ttl_expires():
    logger = logging.getLogger('datahub.core.queues.health_check')
    now = datetime.utcnow()
    with mock.patch.object(logger, 'info') as mock_info:
        show_health_status_for_jobs(
            now,
            [
                '34e8ef6e-4efb-11ed-bdc3-0242ac120002',
                '34e8f342-4efb-11ed-bdc3-0242ac120002',
                '34e8f59a-4efb-11ed-bdc3-0242ac120002',
            ],
        )
        assert 'succeeded to update 3' in str(mock_info.call_args_list)


@mock.patch('datahub.core.queues.health_check.DataHubScheduler.job')
def test_should_throw_retry_error_if_busy(scheduler_job):
    scheduler_job.return_value = mock.Mock(
        id='34e8f59a-4efb-11ed-bdc3-0242ac120002',
        is_finished=False,
        is_failed=False,
    )

    now = datetime.utcnow()

    with pytest.raises(RetryError):
        show_health_status_for_jobs(
            now,
            [
                '34e8f59a-4efb-11ed-bdc3-0242ac120002',
            ],
        )
