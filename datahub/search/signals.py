from logging import getLogger

from datahub.core.thread_pool import submit_to_thread_pool
from datahub.search import elasticsearch

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
        self.signal = signal
        self.sender = sender
        self._receiver_func = receiver_func

    @property
    def _dispatch_uid(self):
        return (f'{id(self.signal):x}'
                f'__{self._receiver_func.__module__}.{self._receiver_func.__name__}'
                f'__{self.sender.__name__}')

    def connect(self):
        """Connects the signal receiver."""
        self.signal.connect(
            self._receiver_func,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid
        )

    def disconnect(self):
        """Disconnects the signal receiver."""
        self.signal.disconnect(
            self._receiver_func,
            sender=self.sender,
            dispatch_uid=self._dispatch_uid
        )


def _sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    instance = db_model.objects.get(pk=pk)
    doc = search_model.es_document(instance)
    elasticsearch.bulk(actions=(doc, ), chunk_size=1)


def sync_es(search_model, db_model, pk):
    """Sync to ES by instance pk and type."""
    return submit_to_thread_pool(_sync_es, search_model, db_model, pk)
