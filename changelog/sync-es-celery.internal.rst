The ``sync_es`` management command was updated to use Celery.

The ``--batch_size`` argument was removed as it is rarely used and isn't currently supported by the Celery task.
