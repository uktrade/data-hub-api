from logging import getLogger

from celery import shared_task
from django.apps import apps
from django.db.models import NOT_PROVIDED, Subquery


logger = getLogger(__name__)


@shared_task(acks_late=True)
def replace_null_with_default(model_label, field_name, default=None, batch_size=5000):
    """
    Task that replaces NULL values for a model field with the default argument if specified
    or the field's default value otherwise.

    This is designed to perform updates in small batches to avoid lengthy locks on a large
    number of rows.
    """
    model = apps.get_model(model_label)
    field = model._meta.get_field(field_name)

    resolved_default = default  # so that the input is not changed
    if resolved_default is None:
        if field.default in (NOT_PROVIDED, None):
            raise ValueError(f'{field_name} does not have a non-null default value')
        resolved_default = field.default

    if callable(resolved_default):
        raise ValueError(f'callable defaults for {field_name} are not supported')

    if not field.null:
        raise ValueError(f'{field_name} is not nullable')

    # Unevaluated subquery to select a batch of rows
    subquery = model.objects.filter(
        **{field_name: None},
    ).values(
        'pk',
    )[:batch_size]

    # Update the batch of rows to use the default value instead
    num_updated = model.objects.filter(
        pk__in=Subquery(subquery),
    ).update(
        **{field_name: resolved_default},
    )

    logger.info(
        f'NULL replaced with {resolved_default!r} for {num_updated} objects, model {model_label}, '
        f'field {field_name}',
    )

    # If there are definitely no more rows needing updating, return
    if num_updated < batch_size:
        return

    # Schedule another task to update another batch of rows
    replace_null_with_default.apply_async(
        args=(model_label, field_name),
        kwargs={'default': default, 'batch_size': batch_size},
    )
