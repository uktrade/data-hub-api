from logging import getLogger

from celery import shared_task
from django.apps import apps
from django.db.models import (
    BooleanField,
    Case,
    Exists,
    ExpressionWrapper,
    NOT_PROVIDED,
    OuterRef,
    Q,
    Subquery,
    When,
)
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.db.transaction import atomic
from django_pglocks import advisory_lock

from datahub.company.models import Company


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


@shared_task(acks_late=True)
def populate_company_address_fields(batch_size=5000):
    """
    Task to populate company address fields from trading address or
    registered address whichever is defined.
    """
    # Coalesce makes sure that both NULL and '' values are treated equally
    base_queryset = Company.objects.annotate(
        address_1_normalised=Coalesce('address_1', Value('')),
        address_town_normalised=Coalesce('address_town', Value('')),
        trading_address_1_normalised=Coalesce('trading_address_1', Value('')),
        trading_address_town_normalised=Coalesce('trading_address_town', Value('')),
        registered_address_1_normalised=Coalesce('registered_address_1', Value('')),
        registered_address_2_normalised=Coalesce('registered_address_2', Value('')),
        registered_address_town_normalised=Coalesce('registered_address_town', Value('')),
        registered_address_county_normalised=Coalesce('registered_address_county', Value('')),
        registered_address_postcode_normalised=Coalesce('registered_address_postcode', Value('')),
        has_valid_trading_address=ExpressionWrapper(
            ~Q(trading_address_1_normalised='')
            & ~Q(trading_address_town_normalised='')
            & Q(trading_address_country__isnull=False),
            output_field=BooleanField(),
        ),
        has_registered_address=ExpressionWrapper(
            ~Q(registered_address_1_normalised='')
            | ~Q(registered_address_2_normalised='')
            | ~Q(registered_address_town_normalised='')
            | ~Q(registered_address_postcode_normalised='')
            | ~Q(registered_address_county_normalised='')
            | Q(registered_address_country__isnull=False),
            output_field=BooleanField(),
        ),
    )

    # Unevaluated subquery to select a batch of records
    subquery = base_queryset.filter(
        Q(has_registered_address=True) | Q(has_valid_trading_address=True),
        address_1_normalised='',
        address_town_normalised='',
        address_country__isnull=True,
    ).values(
        'pk',
    )[:batch_size]

    num_updated = base_queryset.filter(
        pk__in=Subquery(subquery),
    ).update(
        address_1=Case(
            When(has_valid_trading_address=True, then='trading_address_1'),
            default='registered_address_1',
        ),
        address_2=Case(
            When(has_valid_trading_address=True, then='trading_address_2'),
            default='registered_address_2',
        ),
        address_town=Case(
            When(has_valid_trading_address=True, then='trading_address_town'),
            default='registered_address_town',
        ),
        address_county=Case(
            When(has_valid_trading_address=True, then='trading_address_county'),
            default='registered_address_county',
        ),
        address_postcode=Case(
            When(has_valid_trading_address=True, then='trading_address_postcode'),
            default='registered_address_postcode',
        ),
        address_country=Case(
            When(has_valid_trading_address=True, then='trading_address_country'),
            default='registered_address_country',
        ),
    )

    logger.info(f'Finished - populated {num_updated} companies')

    # If there are definitely no more rows needing updating, return
    if num_updated < batch_size:
        return

    # Schedule another task to update another batch of rows
    populate_company_address_fields.apply_async(
        kwargs={'batch_size': batch_size},
    )


@shared_task(acks_late=True)
def copy_foreign_key_to_m2m_field(
    model_label,
    source_fk_field_name,
    target_m2m_field_name,
    batch_size=5000,
):
    """
    Task that copies non-null values from a foreign key to a to-many field (for objects where the
    to-many field is empty).

    Usage example:

        copy_foreign_key_to_m2m_field.apply_async(
            args=('interaction.Interaction', 'contact', 'contacts'),
        )

    Note: This does not create reversion revisions on the model referenced by model_label. For new
    fields, the new versions would simply show the new field being added, so would not be
    particularly useful. If you do need revisions to be created, this task is not suitable.
    """
    lock_name = (
        f'leeloo-copy_foreign_key_to_m2m_field-{model_label}-{source_fk_field_name}'
        f'-{target_m2m_field_name}'
    )

    with advisory_lock(lock_name, wait=False) as lock_held:
        if not lock_held:
            logger.warning(
                f'Another copy_foreign_key_to_m2m_field task is in progress for '
                f'({model_label}, {source_fk_field_name}, {target_m2m_field_name}). Aborting...',
            )
            return

        num_processed = _copy_foreign_key_to_m2m_field(
            model_label,
            source_fk_field_name,
            target_m2m_field_name,
            batch_size=batch_size,
        )

        # If there are definitely no more rows needing processing, return
        if num_processed < batch_size:
            return

        # Schedule another task to update another batch of rows.
        # This must be outside of the atomic block, otherwise it will probably run before the
        # current changes have been committed.
        copy_foreign_key_to_m2m_field.apply_async(
            args=(model_label, source_fk_field_name, target_m2m_field_name),
            kwargs={'batch_size': batch_size},
        )


@atomic
def _copy_foreign_key_to_m2m_field(
    model_label,
    source_fk_field_name,
    target_m2m_field_name,
    batch_size=5000,
):
    """
    The main logic for the copy_foreign_key_to_m2m_field task.

    Processes a single batch in a transaction.
    """
    model = apps.get_model(model_label)
    source_fk_field = model._meta.get_field(source_fk_field_name)
    target_m2m_field = model._meta.get_field(target_m2m_field_name)
    m2m_model = target_m2m_field.remote_field.through
    # e.g. 'interaction_id' for Interaction.contacts
    m2m_column_name = target_m2m_field.m2m_column_name()
    # e.g. 'contact_id' for Interaction.contacts
    m2m_reverse_column_name = target_m2m_field.m2m_reverse_name()

    # Select a batch of rows. The rows are locked to avoid race conditions.
    batch_queryset = model.objects.select_for_update().annotate(
        has_m2m_values=Exists(
            m2m_model.objects.filter(**{m2m_column_name: OuterRef('pk')}),
        ),
    ).filter(
        **{
            f'{source_fk_field_name}__isnull': False,
            'has_m2m_values': False,
        },
    ).values(
        'pk',
        source_fk_field.attname,
    )[:batch_size]

    objects_to_create = [
        m2m_model(
            **{
                m2m_column_name: row['pk'],
                m2m_reverse_column_name: row[source_fk_field.attname],
            },
        ) for row in batch_queryset
    ]

    # Create many-to-many objects for the batch
    created_objects = m2m_model.objects.bulk_create(objects_to_create)
    num_created = len(created_objects)

    logger.info(
        f'{num_created} {model_label}.{target_m2m_field_name} many-to-many objects created',
    )

    return len(objects_to_create)
