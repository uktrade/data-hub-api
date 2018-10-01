from contextlib import contextmanager
from logging import getLogger

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

    def __init__(self, signal, sender, receiver_func):
        """Initialises the instance."""
        self.is_connected = False
        self.signal = signal
        self.sender = sender
        self._receiver_func = receiver_func

    @property
    def _dispatch_uid(self):
        return (
            f'{id(self.signal):x}'
            f'__{self._receiver_func.__module__}.{self._receiver_func.__name__}'
            f'__{self.sender.__name__}'
        )

    def connect(self):
        """Connects the signal receiver."""
        self.signal.connect(
            self._receiver_func,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid,
        )
        self.is_connected = True

    def disconnect(self):
        """Disconnects the signal receiver."""
        self.signal.disconnect(
            self._receiver_func,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid,
        )
        self.is_connected = False


@contextmanager
def disable_search_signal_receivers(model):
    """
    Context manager that disables search signals receivers for a particular model.

    This disables any signal receivers for that model in all search apps, not just the search
    app corresponding to that model.
    """
    signal_receivers = [
        receiver for search_app in get_search_apps()
        for receiver in search_app.get_signal_receivers()
        if receiver.sender == model and receiver.is_connected
    ]

    for receiver in signal_receivers:
        receiver.disconnect()

    try:
        yield
    finally:
        for receiver in signal_receivers:
            receiver.connect()
