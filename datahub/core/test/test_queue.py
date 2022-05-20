import pytest

from datahub.core.queue import DataHubQueue


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


@pytest.fixture(autouse=True)
def reset_spy():
    Spy.reset()


@pytest.fixture(name='queue')
def around_each():
    with DataHubQueue('burst-no-fork') as queue:
        try:
            yield queue
        finally:
            queue.clear()


def test_can_queue_one_thing(queue: DataHubQueue):
    queue.enqueue('test-short-running', Spy.queue_handler)
    queue.work('test-short-running')
    assert Spy.called
    assert Spy.params[0] == ()


def test_can_queue_one_thing_with_arguments(queue: DataHubQueue):
    queue.enqueue('test-short-running', Spy.queue_handler, 'arg1', 'arg2', test=True)
    queue.work('test-short-running')
    assert Spy.called
    assert Spy.params[0] == ('arg1', 'arg2')
    assert Spy.keywords[0] == {'test': True}


def test_does_not_process_for_different_queue(queue: DataHubQueue):
    queue.enqueue('dead-letter', Spy.queue_handler)
    queue.work('test-short-running')
    assert not Spy.called


def test_can_clear_all_queues(queue: DataHubQueue):
    queue.enqueue('dead-letter', Spy.queue_handler)
    queue.enqueue('111', Spy.queue_handler)
    queue.enqueue('222', Spy.queue_handler)
    queue.clear()
    queue.work('dead-letter')
    queue.work('111')
    queue.work('222')
    assert not Spy.called


def test_can_process_multiple_queues_in_correct_priority_order(queue: DataHubQueue):
    queue.enqueue('dead-letter', Spy.queue_handler, 1)
    queue.enqueue('test-short-running', Spy.queue_handler, True)
    queue.enqueue('test-long-running', Spy.queue_handler, False)
    queue.work('test-short-running', 'test-long-running', 'dead-letter')
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
