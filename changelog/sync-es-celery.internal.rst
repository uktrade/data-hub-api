The ``sync_es`` management command was updated to use Celery.

By default, the Celery task runs asynchronously. ``--foreground`` can be passed to run the Celery task synchronously (without Celery running).

The ``--batch_size`` argument was removed as it is rarely used and isn't currently supported by the Celery task.
