from unittest.mock import Mock

import pytest
from rq import Retry

from datahub.core.queue import DataHubQueue, job_scheduler


class Spy:
    called = False
    times = 0
    params = []
    keywords = []

    @staticmethod
    def reset():
        Spy.called = False
        Spy.times = 0
        Spy.params = []
        Spy.keywords = []

    @staticmethod
    def queue_handler(*args, **kwargs):
        Spy.called = True
        Spy.times += 1
        Spy.params.append(args)
        Spy.keywords.append(kwargs)

    @staticmethod
    def queue_handler_with_error():
        raise Exception('Spanner in the works')


@pytest.fixture(autouse=True)
def reset_spy():
    Spy.reset()


def test_can_queue_one_thing(async_queue: DataHubQueue):
    async_queue.enqueue('one-running', Spy.queue_handler)
    async_queue.work('one-running')
    assert Spy.called
    assert Spy.params[0] == ()


def test_can_queue_one_thing_with_arguments(async_queue: DataHubQueue):
    async_queue.enqueue('running-with-args', Spy.queue_handler, 'arg1', 'arg2', test=True)
    async_queue.work('running-with-args')
    assert Spy.called
    assert Spy.params[0] == ('arg1', 'arg2')
    assert Spy.keywords[0] == {'test': True}


def test_does_not_process_for_different_queue(async_queue: DataHubQueue):
    async_queue.enqueue('dead-letter', Spy.queue_handler)
    async_queue.work('not-dead-letter')
    assert not Spy.called


def test_can_clear_all_queues(async_queue: DataHubQueue):
    async_queue.enqueue('dead-letter', Spy.queue_handler)
    async_queue.enqueue('111', Spy.queue_handler)
    async_queue.enqueue('222', Spy.queue_handler)
    async_queue.clear()
    async_queue.work('dead-letter')
    async_queue.work('111')
    async_queue.work('222')
    assert not Spy.called


def test_can_process_multiple_queues_in_correct_priority_order(async_queue: DataHubQueue):
    async_queue.enqueue('queue1', Spy.queue_handler, 1)
    async_queue.enqueue('queue2', Spy.queue_handler, True)
    async_queue.enqueue('queue3', Spy.queue_handler, False)
    async_queue.work('queue2', 'queue3', 'queue1')
    assert Spy.times == 3
    assert Spy.params[0] == (True,)
    assert Spy.params[1] == (False,)
    assert Spy.params[2] == (1,)


def test_cleans_up_redis_connection():
    with DataHubQueue('burst-no-fork') as queue:
        try:
            queue.enqueue('123', Spy.queue_handler)
            queue.work('123')
        finally:
            queue.clear()

    assert None is queue._connection.connection


def test_job_retry_with_errors_will_reschedule_with_three_tries(async_queue: DataHubQueue):
    job = async_queue.enqueue(
        queue_name='will_fail',
        function=Spy.queue_handler_with_error,
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


def test_task_scheduler_generates_job(queue: DataHubQueue):
    job = job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        retry_intervals=[1, 2],
        is_burst=True,
    )

    assert job is not None
    assert job.retries_left == 3
    assert job.retry_intervals == [1, 2]


def test_task_scheduler_configures_queues(queue: DataHubQueue):
    job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        is_burst=True,
    )

    assert Spy.called
    assert Spy.params[0] == ('arg1', 'arg2')
    assert Spy.keywords[0] == {'test': True}


def test_task_scheduler_runs_as_expected_not_in_test_mode(
    monkeypatch,
    queue: DataHubQueue,
):
    monkeypatch.setattr('datahub.core.queue.settings.IS_TEST', False)
    datahub_queue_mock = queue_setup(monkeypatch)
    Spy.reset()
    job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='569',
        max_retries=3,
        is_burst=True,
    )

    queue.work('569')

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 3
    datahub_queue_mock.assert_called_with(
        queue_name='569',
        function=Spy.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
    )


def test_datahub_enque_is_configured_with_correct_default_number_of_retries_and_intervals(
    monkeypatch,
):
    datahub_queue_mock = queue_setup(monkeypatch)
    job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        is_burst=True,
    )

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 3
    assert retry_arg.intervals == [0]
    datahub_queue_mock.assert_called_with(
        queue_name='test-234',
        function=Spy.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
    )


def test_datahub_enque_is_configured_with_retry_backoff_for_two_retries(monkeypatch):
    datahub_queue_mock = queue_setup(monkeypatch)
    job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=2,
        retry_backoff=True,
    )

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 2
    assert retry_arg.intervals == [1, 4]
    datahub_queue_mock.assert_called_with(
        queue_name='test-234',
        function=Spy.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
    )


def test_datahub_enque_is_configured_with_retry_backoff_as_number(monkeypatch):
    datahub_queue_mock = queue_setup(monkeypatch)

    job_scheduler(
        function=Spy.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        retry_backoff=30,
    )

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 3
    assert retry_arg.intervals == [30, 961, 1024]
    datahub_queue_mock.assert_called_with(
        queue_name='test-234',
        function=Spy.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
    )


def queue_setup(monkeypatch):
    datahub_queue_mock = Mock()
    monkeypatch.setattr('datahub.core.queue.DataHubQueue.enqueue', datahub_queue_mock)
    return datahub_queue_mock


def get_retry(datahub_queue_mock):
    return datahub_queue_mock.call_args_list[-1][-1]['retry']
