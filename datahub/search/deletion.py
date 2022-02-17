from collections import defaultdict
from contextlib import contextmanager

from django.db import transaction
from django.db.models.signals import post_delete, pre_delete

from datahub.core.exceptions import DataHubError
from datahub.search.apps import get_search_app_by_model, get_search_apps
from datahub.search.opensearch import bulk, get_client
from datahub.search.signals import SignalReceiver


BULK_DELETION_TIMEOUT_SECS = 300
BULK_CHUNK_SIZE = 10000


def delete_documents(index, docs):
    """
    Deletes `docs` from `index`.

    :raises DataHubError: in case of non 404 errors
    """
    delete_actions = (
        _create_delete_action(index, doc['_id'])
        for doc in docs
    )

    _, errors = bulk(
        actions=delete_actions,
        chunk_size=BULK_CHUNK_SIZE,
        request_timeout=BULK_DELETION_TIMEOUT_SECS,
        raise_on_error=False,
    )

    non_404_errors = [error for error in errors if error['delete']['status'] != 404]
    if non_404_errors:
        raise DataHubError(
            f'Errors during an OpenSearch bulk deletion operation: {non_404_errors!r}',
        )


def _create_delete_action(_index, _id):
    return {
        '_op_type': 'delete',
        '_index': _index,
        '_id': _id,
    }


class Collector:
    """
    Collects all the deleted django objects so that they can be deleted from OpenSearch.

    Most of the time you will want to use the context manager/decorator
    `update_opensearch_after_deletions` instead.

    Usage:

        collector = Collector()
        collector.connect()  # starts listening to post_delete signals

        # delete django objects

        collector.disconnect()  # stops listening to post_delete signals

        collector.delete_from_opensearch()  # deletes the collected objects from OpenSearch

    WARNING: this temporarily disable existing post_delete and pre_delete signal
    receivers defined in all the SearchApps to avoid side effects.
    Also, be careful when starting a transaction (e.g. with `transaction.atomic()`) and
    catching any exception in it. OpenSearch deletions would still happen because the
    collector would not be aware of any caught error.
    """

    def __init__(self):
        """Initialises the object."""
        self.signal_receivers_to_add = []
        self.signal_receivers_to_disable = []
        self.deletions = defaultdict(list)

        for search_app in get_search_apps():
            model = search_app.queryset.model

            # set up the receivers to add when collecting the deleted objects
            self.signal_receivers_to_add.append(
                SignalReceiver(post_delete, model, self._collect),
            )

            # get the existing post/pre_delete receivers that need to be
            # disabled in the meantime
            for receiver in search_app.get_signal_receivers():
                if receiver.signal in (post_delete, pre_delete):
                    self.signal_receivers_to_disable.append(receiver)

    def connect(self):
        """Starts listening to post_delete signals on all search models."""
        for receiver in self.signal_receivers_to_add:
            receiver.connect()

        for receiver in self.signal_receivers_to_disable:
            receiver.disable()

    def disconnect(self):
        """Starts listening to post_delete signals on all search models."""
        for receiver in self.signal_receivers_to_add:
            receiver.disconnect()

        for receiver in self.signal_receivers_to_disable:
            receiver.enable()

    def _collect(self, instance):
        """Logic that gets run on post_delete."""
        model = instance.__class__
        search_model = get_search_app_by_model(model).search_model

        doc = search_model.to_document(instance, include_index=False, include_source=False)
        self.deletions[model].append(doc)

    def _delete_from_opensearch(self):
        for model, docs in self.deletions.items():
            search_app = get_search_app_by_model(model)
            delete_documents(search_app.search_model.get_write_alias(), docs)

    def delete_from_opensearch(self):
        """Deletes all the deleted django models from OpenSearch."""
        transaction.on_commit(self._delete_from_opensearch)


@contextmanager
def update_opensearch_after_deletions():
    """
    Returns a context manager that can be used to automatically delete from OpenSearch
    all the django objects deleted in the block.
    It can be used as a decorator as well.

    This works by listening to the `post_delete` django signal, collecting all the deleted
    django objects and deleting all of them from OpenSearch in bulk when exiting from the
    context manager.

    WARNING: this temporarily disable existing post_delete and pre_delete signal
    receivers defined in all the SearchApps to avoid side effects.
    Also, be careful when starting a transaction (e.g. with `transaction.atomic()`) and
    catching any exception in it. OpenSearch deletions would still happen because the
    context manager would not be aware of any caught error.
    """
    collector = Collector()
    collector.connect()

    try:
        yield collector
    finally:
        collector.disconnect()

    collector.delete_from_opensearch()


def delete_document(model, document_id, indices=None, ignore_404_responses=True):
    """Deletes specified model's document."""
    client = get_client()
    if indices is None:
        indices = [model.get_write_alias()]
    ignored_response_statuses = (404,) if ignore_404_responses else ()

    for index in indices:
        client.delete(
            index=index,
            id=document_id,
            ignore=ignored_response_statuses,
        )
