from collections import defaultdict

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_init,
    post_migrate,
    post_save,
    pre_delete,
    pre_init,
    pre_migrate,
    pre_save,
)


class DisableSignals:
    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            pre_init,
            post_init,
            pre_save,
            post_save,
            pre_delete,
            post_delete,
            pre_migrate,
            post_migrate,
            m2m_changed,
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in list(self.stashed_signals):
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]


def random_object_from_queryset(queryset):
    """Returns a random object for a queryset."""
    return queryset.order_by('?').first()


def print_progress(
    iteration, total, prefix='', suffix='', decimals=1, bar_length=50,
):
    """Call in a loop to create a progress bar in the console.

    Args:
        iteration (int): current iteration
        total (int): total iterations
        prefix (str, optional): prefix string. Defaults to ''.
        suffix (str, optional): suffix string. Defaults to ''.
        decimals (int, optional): positive number of decimals in % complete. Defaults to 1.
        bar_length (int, optional): character length of bar. Defaults to 50.
    """
    percent = round(100 * (iteration / total), decimals)
    filled_length = int(round(bar_length * iteration / total))
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    print(f'{prefix} |{bar}| {percent}% {suffix}')  # noqa
