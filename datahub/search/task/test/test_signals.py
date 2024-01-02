from unittest import mock

import pytest

from opensearchpy.exceptions import NotFoundError

from datahub.search.task.apps import TaskSearchApp
from datahub.task.test.factories import TaskFactory


pytestmark = pytest.mark.django_db


def _get_documents(setup_opensearch, pk):
    return setup_opensearch.get(
        index=TaskSearchApp.search_model.get_read_alias(),
        id=pk,
    )


def test_new_task_synced(opensearch_with_signals):
    """Test that new adviser is synced to OpenSearch."""
    task = TaskFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=TaskSearchApp.search_model.get_write_index(),
        id=task.pk,
    )


@pytest.mark.parametrize(
    'task_factory,expected_in_index,expected_to_call_delete',
    (
        (TaskFactory, True, True),
    ),
)
def test_delete_from_opensearch(
    task_factory,
    expected_in_index,
    expected_to_call_delete,
    opensearch_with_signals,
):
    """
    Test that when a task is deleted from db it is also
    calls delete document to delete from OpenSearch.
    """
    task = task_factory()
    opensearch_with_signals.indices.refresh()

    if expected_in_index:
        assert _get_documents(opensearch_with_signals, task.pk)
    else:
        with pytest.raises(NotFoundError):
            assert _get_documents(opensearch_with_signals, task.pk) is None

    with mock.patch(
        'datahub.search.task.signals.delete_document',
    ) as mock_delete_document:
        task.delete()
        opensearch_with_signals.indices.refresh()
        assert mock_delete_document.called == expected_in_index
