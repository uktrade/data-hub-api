from django.db import transaction
from django.db.models.signals import post_save

from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async
from datahub.search.task import TaskSearchApp
from datahub.task.models import Task as DBTask


def sync_task_to_opensearch(instance):
    """Sync task to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(TaskSearchApp, instance.pk),
    )


receivers = (SignalReceiver(post_save, DBTask, sync_task_to_opensearch),)