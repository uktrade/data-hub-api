from contextlib import contextmanager
from logging import getLogger
from threading import local

from datahub.search.apps import get_search_apps

logger = getLogger(__name__)


class SignalReceiver:
    """
    Helper class for managing signal receivers in search apps.

    Instances of this class are intended to be used with the automatic signal receiver
    connection and disconnection mechanism of the search apps.

    The mod_signals attribute of a search app specifies the module containing signals for that app.
    (This defaults to the signals submodule of that app.)

    The receivers attribute of that module should be a sequence of SignalReceiver instances which
    are automatically connected and disconnected as needed.
    """

    def __init__(self, signal, sender, receiver_func, forward_kwargs=False):
        """Initialises the instance."""
        self.is_connected = False
        self.search_app = None
        self.signal = signal
        self.sender = sender
        self.forward_kwargs = forward_kwargs
        self._receiver_func = receiver_func
        self._thread_locals = local()

    @property
    def _dispatch_uid(self):
        return (
            f'{id(self.signal):x}'
            f'__{self._receiver_func.__module__}.{self._receiver_func.__name__}'
            f'__{self.sender.__name__}'
        )

    def connect(self):
        """Connects the signal receiver (for all threads)."""
        self.signal.connect(
            self.on_signal_received,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid,
        )
        self.is_connected = True

    def disconnect(self):
        """Disconnects the signal receiver (for all threads)."""
        self.signal.disconnect(
            self.on_signal_received,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid,
        )
        self.is_connected = False

    def enable(self):
        """
        Enables a previously disabled signal receiver for the current thread.

        This only affects connected signal receivers. Connected signal receivers
        default to being enabled.
        """
        self._thread_locals.enabled = True

    def disable(self):
        """
        Disables a signal receiver for the current thread.

        This only affects connected signal receivers.
        """
        self._thread_locals.enabled = False

    @property
    def is_enabled(self):
        """
        Whether the signal receiver is enabled for the current thread.

        A signal receiver must also be connected for it to receive signals.
        """
        return getattr(self._thread_locals, 'enabled', True)

    def on_signal_received(self, sender, instance, **kwargs):
        """Callback function passed to the signal."""
        if self.is_enabled:
            if self.forward_kwargs:
                self._receiver_func(instance, **kwargs)
            else:
                self._receiver_func(instance)


@contextmanager
def disable_search_signal_receivers(sender):
    """
    Context manager that disables search signals receivers for a particular sender (e.g. a model).

    This disables any signal receivers for the specified sender in all search apps (and not just
    the search app corresponding to the specified sender). For example, specifying Company will
    also stop contacts from being synced when a companies is modified.
    """
    signal_receivers = [
        receiver for search_app in get_search_apps()
        for receiver in search_app.get_signal_receivers()
        if receiver.sender == sender and receiver.is_enabled
    ]

    for receiver in signal_receivers:
        receiver.disable()

    try:
        yield
    finally:
        for receiver in signal_receivers:
            receiver.enable()
