from unittest import mock

import pytest


@pytest.fixture
def mock_export_win_tasks_notify_gateway(monkeypatch):
    mock_notify_gateway = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.tasks.notify_gateway',
        mock_notify_gateway,
    )
    return mock_notify_gateway


@pytest.fixture
def mock_export_win_serializer_notify(monkeypatch):
    mock_notify = mock.Mock()
    monkeypatch.setattr(
        'datahub.export_win.serializers.notify_export_win_email_by_rq_email',
        mock_notify,
    )
    return mock_notify
