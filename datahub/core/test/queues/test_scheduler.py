import pytest
from django.conf import settings
from rq import Retry

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
    assert job.is_scheduled is True
    assert job.retries_left == 3
    assert job.retry_intervals == [1, 4, 16]


def test_should_be_in_the_testing_environment():
    assert settings.IS_TEST is True


def test_can_schedule_a_cron_job_every_minute(queue: DataHubScheduler):
    every_minute = '* * * * *'
    job = queue.cron('cron-schedule', every_minute, PickleableMock.queue_handler)

    assert job.meta['cron_string'] == every_minute
    assert job.meta['use_local_timezone'] is False
