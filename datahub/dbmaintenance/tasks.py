from logging import getLogger

from celery import shared_task
from django.apps import apps
from django.db.models import BooleanField, Case, ExpressionWrapper, NOT_PROVIDED, Q, Subquery, When
from django.db.models import Value
from django.db.models.functions import Coalesce

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
