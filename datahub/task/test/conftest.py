import pytest

from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save


@pytest.fixture(scope='module', autouse=True)
def mute_task_signals(request):
    # By default this disables all signals for tasks. If a test needs the signals enabled then
    # adding `pytest.mark.enable_task_signals` will re-enable them
    if 'enable_task_signals' in request.keywords:
        yield
    else:
        signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
        restore = {}
        for signal in signals:
            restore[signal] = signal.receivers
            signal.receivers = []

        def restore_signals():
            for signal, receivers in restore.items():
                signal.sender_receivers_cache.clear()
                signal.receivers = receivers

        request.addfinalizer(restore_signals)
        yield
