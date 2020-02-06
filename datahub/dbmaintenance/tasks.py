from logging import getLogger

from celery import shared_task
from django.apps import apps
from django.db.models import Exists, NOT_PROVIDED, OuterRef, Subquery
from django.db.transaction import atomic
from django_pglocks import advisory_lock

from datahub.company.models import Company, CompanyExportCountry

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
    #
    # This must be outside of the atomic block, otherwise it will probably run before the
    # current changes have been committed.
    #
    # (Similarly, the lock should also be released before the next task is scheduled.)
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

    has_no_m2m_values_subquery = ~Exists(
        m2m_model.objects.filter(**{m2m_column_name: OuterRef('pk')}),
    )

    # Select a batch of rows. The rows are locked to avoid race conditions.
    batch_queryset = model.objects.select_for_update().filter(
        has_no_m2m_values_subquery,
        **{
            f'{source_fk_field_name}__isnull': False,
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


@shared_task(acks_late=True)
def copy_export_countries_to_company_export_country_model(
    status,
    batch_size=5000,
):
    """
    Task that copies all export countries from Company model to CompanyExportCountry
    """
    key_switch = {
        'future_interest': 'future_interest_countries',
        'currently_exporting': 'export_to_countries',
    }

    num_updated = _copy_export_countries(key_switch[status], status, batch_size)

    # If there are definitely no more rows needing processing, return
    if num_updated < batch_size:
        return

    copy_export_countries_to_company_export_country_model.apply_async(
        kwargs={
            'batch_size': batch_size,
            'status': status,
        },
    )


@atomic
def _copy_export_countries(key, status, batch_size):
    """
    Main logic for copying export companies from Company model to
    CompanyExportCountry one
    """
    export_countries = _get_company_countries(key, status, batch_size)
    num_updated = _copy_company_countries(
        key,
        export_countries,
        status,
    )

    logger.info(
        f'Company.{key} copied to CompanyExportCountry '
        f'for {num_updated} Company export countries',
    )

    return num_updated


def _get_company_countries(source_field, status, batch_size):
    no_company_country_subquery = ~Exists(
        CompanyExportCountry.objects.filter(
            company_id=OuterRef('pk'),
            status=status,
        ),
    )
    has_existing_old_countries = Exists(
        Company.objects.filter(
            **{
                'pk': OuterRef('pk'),
                f'{source_field}__isnull': False,
            },
        ),
    )
    batch_queryset = Company.objects.select_for_update().filter(
        no_company_country_subquery,
        has_existing_old_countries,
    ).only(
        'pk',
    )
    return batch_queryset[:batch_size]


def _copy_company_countries(source_field, company_with_uncopied_countries, status):
    company_export_country_model = apps.get_model('company', 'CompanyExportCountry')

    num_updated = 0

    for company in company_with_uncopied_countries:
        num_updated += 1

        for country in getattr(company, source_field).all():
            export_country, created = company_export_country_model.objects.get_or_create(
                company=company,
                country=country,
                defaults={
                    'status': status,
                },
            )
            if not created and export_country.status != status:
                export_country.status = status
                export_country.save()

    return num_updated
