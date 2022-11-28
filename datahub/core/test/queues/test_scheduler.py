from unittest.mock import call, MagicMock

import pytest
from django.conf import settings
from rq import Retry

from datahub.core.queues.constants import EVERY_MINUTE
from datahub.core.queues.scheduler import DataHubScheduler


class PickleableMock:
    called = False
    times = 0
    params = []
    keywords = []

    def __init__(self):
        PickleableMock.reset()

    @staticmethod
    def reset():
        PickleableMock.called = False
        PickleableMock.times = 0
        PickleableMock.params = []
        PickleableMock.keywords = []

    @staticmethod
    def queue_handler(*args, **kwargs):
        PickleableMock.called = True
        PickleableMock.times += 1
        PickleableMock.params.append(args)
        PickleableMock.keywords.append(kwargs)

    @staticmethod
    def queue_handler_with_error():
        raise Exception('Spanner in the works')


@pytest.fixture(autouse=True)
def reset_spy():
    PickleableMock.reset()


def test_can_queue_one_thing(async_queue: DataHubScheduler):
    async_queue.enqueue('one-running', PickleableMock.queue_handler)
    async_queue.work('one-running', with_scheduler=False)
    assert PickleableMock.called
    assert PickleableMock.params[0] == ()


def test_can_queue_one_thing_with_arguments(async_queue: DataHubScheduler):
    async_queue.enqueue(
        'running-with-args',
        PickleableMock.queue_handler,
        'arg1',
        'arg2',
        test=True,
    )
    async_queue.work('running-with-args', with_scheduler=True)
    assert PickleableMock.called
    assert PickleableMock.params[0] == ('arg1', 'arg2')
    assert PickleableMock.keywords[0] == {'test': True}


def test_does_not_process_for_different_queue(async_queue: DataHubScheduler):
    async_queue.enqueue('dead-letter', PickleableMock.queue_handler)
    async_queue.work('not-dead-letter')
    assert not PickleableMock.called


def test_can_clear_all_queues(async_queue: DataHubScheduler):
    async_queue.enqueue('dead-letter', PickleableMock.queue_handler)
    async_queue.enqueue('111', PickleableMock.queue_handler)
    async_queue.enqueue('222', PickleableMock.queue_handler)
    async_queue.clear()
    async_queue.work('dead-letter')
    async_queue.work('111')
    async_queue.work('222')
    assert not PickleableMock.called


def test_can_process_multiple_queues_in_correct_priority_order(async_queue: DataHubScheduler):
    async_queue.enqueue('queue1', PickleableMock.queue_handler, 1)
    async_queue.enqueue('queue2', PickleableMock.queue_handler, True)
    async_queue.enqueue('queue3', PickleableMock.queue_handler, False)
    async_queue.work('queue2', 'queue3', 'queue1')
    assert PickleableMock.times == 3
    assert PickleableMock.params[0] == (True,)
    assert PickleableMock.params[1] == (False,)
    assert PickleableMock.params[2] == (1,)


def test_cleans_up_redis_connection():
    with DataHubScheduler('burst-no-fork') as queue:
        try:
            queue.enqueue('123', PickleableMock.queue_handler)
            queue.work('123')
        finally:
            queue.clear()

    assert None is queue._connection.connection


def test_job_retry_with_errors_will_reschedule_with_three_tries(async_queue: DataHubScheduler):
    job = async_queue.enqueue(
        queue_name='will_fail',
        function=PickleableMock.queue_handler_with_error,
        retry=Retry(
            max=3,
            interval=[1, 4, 16],
        ),
    )

    async_queue.work('will_fail')

    assert job is not None
    retrieved_job = async_queue.job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.is_scheduled is True
    assert job.retries_left == 3
    assert job.retry_intervals == [1, 4, 16]


def test_job_not_retried_with_retry_none(async_queue: DataHubScheduler):
    job = async_queue.enqueue(
        queue_name='will_fail',
        function=PickleableMock.queue_handler_with_error,
    )

    async_queue.work('will_fail')

    assert job is not None
    retrieved_job = async_queue.job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.is_scheduled is False
    assert job.retries_left is None
    assert job.retry_intervals is None


def test_should_be_in_the_testing_environment():
    assert settings.IS_TEST is True


def test_can_schedule_a_cron_job_every_minute(queue: DataHubScheduler):
    job = queue.cron(
        'cron-schedule',
        EVERY_MINUTE,
        PickleableMock.queue_handler,
        description='Test cron every minute',
    )

    assert job.meta['cron_string'] == EVERY_MINUTE
    assert job.meta['use_local_timezone'] is False
    assert job.description == 'Test cron every minute'


def test_fork_queue_worker_is_called_with_work_arguments(
    monkeypatch,
    fork_queue: DataHubScheduler,
):
    mock_worker = MagicMock()
    monkeypatch.setattr('datahub.core.queues.scheduler.Worker', mock_worker)

    fork_queue.work('one-running', with_scheduler=False)
    mock_worker.assert_called_with(('one-running',), connection=fork_queue._connection)
    assert call().work(with_scheduler=False) in mock_worker.mock_calls


def test_job_timeout_is_generated_on_job(queue: DataHubScheduler):
    job = queue.enqueue(
        queue_name='123',
        function=PickleableMock.queue_handler,
        job_timeout=600,
    )

    queue.work('123')

    assert job.timeout == 600


def test_purging_queue(async_queue: DataHubScheduler):
    async_queue.enqueue(
        queue_name='purge-test',
        function=PickleableMock.queue_handler,
    )
    assert async_queue.queued_count('purge-test') == 1
    async_queue.work('purge-test')

    async_queue.purge('purge-test')

    assert async_queue.queued_count('purge-test') == 0


def test_purging_fails(
    async_queue: DataHubScheduler,
):
    job = async_queue.enqueue(
        queue_name='will_fail',
        function=PickleableMock.queue_handler_with_error,
        retry=Retry(max=1),
    )
    async_queue.work('will_fail')

    assert async_queue.failed_count('will_fail') == 1
    retrieved_job = async_queue.job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.is_failed is True
    async_queue.purge('will_fail', 'failed')

    assert async_queue.failed_count('will_fail') == 0


def test_purging_scheduled(
    async_queue: DataHubScheduler,
):
    job = async_queue.enqueue(
        queue_name='will_fail',
        function=PickleableMock.queue_handler_with_error,
        retry=Retry(
            max=1,
            interval=[60],
        ),
    )
    async_queue.work('will_fail')
    assert async_queue.scheduled_count('will_fail') >= 1
    retrieved_job = async_queue.job(job.id)
    assert retrieved_job is not None
    assert retrieved_job.is_scheduled is True

    async_queue.purge('will_fail', 'scheduled')

    assert async_queue.scheduled_count('will_fail') == 0


def test_purging_cron_scheduled(
    async_queue: DataHubScheduler,
):
    initial_cron_scheduled_count = async_queue.cron_job_count()
    async_queue.cron(
        queue_name='purge-cron',
        cron=EVERY_MINUTE,
        function=PickleableMock.queue_handler,
    )
    assert async_queue.cron_job_count() == initial_cron_scheduled_count + 1

    async_queue.cancel_cron_jobs()

    assert async_queue.failed_count('will_fail') == 0


def test_job_enqued_is_fetched_in_the_same_state(queue: DataHubScheduler):
    actual_job = queue.enqueue(
        queue_name='job-test',
        function=PickleableMock.queue_handler,
    )

    fetched_job = queue.job(actual_job.id)

    assert fetched_job == actual_job
