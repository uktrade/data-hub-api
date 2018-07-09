from datetime import timedelta
from logging import getLogger
from secrets import token_urlsafe

from dateutil.utils import today
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef
from django.template.defaultfilters import capfirst
from django.utils.timezone import utc

from datahub.search.deletion import update_es_after_deletions

logger = getLogger(__name__)


class OrphanDeletionConfig:
    """
    Defines the config values with related defaults used to determine
    when a record is considered orphan.
    """

    def __init__(
        self,
        days_before_orphaning=30 * 6,  # 6 months
        date_field='modified_on'
    ):
        """Initialises the objects with overridable defaults."""
        self.days_before_orphaning = days_before_orphaning
        self.date_field = date_field


# CONFIGS FOR ALL MODELS ALLOWED TO BE CLEANED UP
ORPHANING_CONFIGS = {
    'company.Contact': OrphanDeletionConfig(),
    'company.Company': OrphanDeletionConfig(),
    'event.Event': OrphanDeletionConfig(date_field='end_date')
}


def get_related_fields(model):
    """
    Returns all the fields of `model` that hold the link between referencing objects
    and the referenced object (`model`).

    :param model: orphaned model class
    :returns: list of fields of `model` that hold references via dependent objects
    """
    return [
        f for f in model._meta.get_fields(include_hidden=True)
        if (f.one_to_many or f.one_to_one or f.many_to_many or f.many_to_one)
        and f.auto_created
        and not f.concrete
        and not f.field.model._meta.auto_created
    ]


def get_unreferenced_objects_query(model):
    """
    :param model: orphaned model class
    :returns: queryset for unreferenced objects
    """
    fields = get_related_fields(model)

    identifiers = [f'ann_{token_urlsafe(6)}' for _ in range(len(fields))]

    qs = model.objects.all()
    for identifier, field in zip(identifiers, fields):
        related_field = field.field
        subquery = related_field.model.objects.filter(
            **{related_field.attname: OuterRef('pk')},
        ).only('pk')
        qs = qs.annotate(**{identifier: Exists(subquery)})

    filter_args = {identifier: False for identifier in identifiers}

    return qs.filter(**filter_args)


class Command(BaseCommand):
    """
    Django command to delete orphaned records for `model`.
    Orphans are `days_before_orphaning` old records without any objects referencing them.

    If the argument `simulate=True` is passed in, the command only simulates the action.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            'model',
            choices=ORPHANING_CONFIGS,
            help='Model to clean up.'
        )
        parser.add_argument(
            '--simulate',
            action='store_true',
            default=False,
            help='If True it only simulates the command and prints the SQL query.',
        )

    @update_es_after_deletions()
    def handle(self, *args, **options):
        """Main logic for the actual command."""
        model_name = options['model']

        model = apps.get_model(model_name)
        config = ORPHANING_CONFIGS[model_name]

        orphaning_datetime = today(tzinfo=utc) - timedelta(config.days_before_orphaning)
        qs = get_unreferenced_objects_query(model)
        qs = qs.filter(
            **{f'{config.date_field}__lt': orphaning_datetime}
        ).order_by('-modified_on')

        model_verbose_name = capfirst(model._meta.verbose_name_plural)
        logger.info(f'{model_verbose_name} to delete: {qs.count()}')

        if options['simulate']:
            logger.info(f'SQL:\n{qs.query}')
        else:
            deleted = qs.delete()
            logger.info(f'{model_verbose_name} deleted: {deleted}')
