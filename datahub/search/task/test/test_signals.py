import pytest


from datahub.search.task.apps import TaskSearchApp
from datahub.task.test.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_new_task_synced(opensearch_with_signals):
    """Test that new adviser is synced to OpenSearch."""
    task = TaskFactory()
    opensearch_with_signals.indices.refresh()

    assert opensearch_with_signals.get(
        index=TaskSearchApp.search_model.get_write_index(),
        id=task.pk,
    )
