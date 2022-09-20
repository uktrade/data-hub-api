from unittest.mock import Mock

from datahub.core.queues.constants import EVERY_MINUTE
from datahub.core.queues.job_scheduler import job_scheduler, retry_backoff_intervals
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.core.test.queues.test_scheduler import PickleableMock


def test_job_scheduler_generates_job(queue: DataHubScheduler):
    job = job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        retry_intervals=[1, 2],
        is_burst=True,
    )

    queue.work('234')

    assert job is not None
    assert job.retries_left == 3
    assert job.retry_intervals == [1, 2]


def test_job_scheduler_configures_queues(queue: DataHubScheduler):
    PickleableMock.reset()
    job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        is_burst=True,
    )

    queue.work('234')

    assert PickleableMock.called
    assert PickleableMock.params[0] == ('arg1', 'arg2')
    assert PickleableMock.keywords[0] == {'test': True}


def test_datahub_enque_is_configured_with_correct_default_number_of_retries_and_intervals(
    monkeypatch,
    queue: DataHubScheduler,
):
    datahub_queue_mock = queue_setup(monkeypatch)
    job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        is_burst=True,
    )

    queue.work('234')

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 3
    assert retry_arg.intervals == [0]
    datahub_queue_mock.assert_called_with(
        queue_name='234',
        function=PickleableMock.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
        job_timeout=180,
    )


def test_datahub_enque_is_configured_with_retry_backoff_for_two_retries(
    monkeypatch,
    queue: DataHubScheduler,
):
    datahub_queue_mock = queue_setup(monkeypatch)
    job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=2,
        retry_backoff=True,
        job_timeout=600,
    )

    queue.work('234')

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 2
    assert retry_arg.intervals == [1, 4]
    datahub_queue_mock.assert_called_with(
        queue_name='234',
        function=PickleableMock.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
        job_timeout=600,
    )


def test_datahub_enque_is_configured_with_retry_backoff_as_number(
    monkeypatch,
    queue: DataHubScheduler,
):
    datahub_queue_mock = queue_setup(monkeypatch)

    job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        queue_name='234',
        max_retries=3,
        retry_backoff=30,
    )

    queue.work('234')

    retry_arg = get_retry(datahub_queue_mock)
    assert retry_arg.max == 3
    assert retry_arg.intervals == [30, 961, 1024]
    datahub_queue_mock.assert_called_with(
        queue_name='234',
        function=PickleableMock.queue_handler,
        args=('arg1', 'arg2'),
        kwargs={'test': True},
        retry=retry_arg,
        job_timeout=180,
    )


def test_retry_backoff_returns_zero_when_turned_off():
    actual = retry_backoff_intervals(
        max_retries=2,
        retry_backoff=False,
        is_backoff_an_int=False,
    )

    assert actual == 0


def test_job_scheduler_creates_cron_jobs(queue: DataHubScheduler):
    existing_job_count = len(list(queue.get_scheduled_jobs()))
    actual_job = job_scheduler(
        function=PickleableMock.queue_handler,
        function_args=('arg1', 'arg2'),
        function_kwargs={'test': True},
        is_burst=True,
        cron=EVERY_MINUTE,
    )

    assert actual_job in queue.get_scheduled_jobs()
    assert len(list(queue.get_scheduled_jobs())) == existing_job_count + 1
    assert actual_job.meta['cron_string'] == EVERY_MINUTE


def queue_setup(monkeypatch):
    datahub_queue_mock = Mock()
    monkeypatch.setattr(
        'datahub.core.queues.scheduler.DataHubScheduler.enqueue',
        datahub_queue_mock,
    )
    return datahub_queue_mock


def get_retry(datahub_queue_mock):
    return datahub_queue_mock.call_args_list[-1][-1]['retry']
