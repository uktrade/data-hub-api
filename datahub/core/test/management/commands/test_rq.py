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


def test_rq_health_check_is_called(monkeypatch):
    mock = PickleableMock()
    monkeypatch.setattr(
        'datahub.core.management.commands.test_rq.queue_health_check',
        mock.handler,
    )

    call_command('test_rq')

    assert mock.called is True
    assert mock.times == 3
