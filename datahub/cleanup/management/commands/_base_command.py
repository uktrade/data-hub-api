from contextlib import ExitStack
from logging import getLogger

from dateutil.utils import today
from django.apps import apps
from django.core.management import BaseCommand
from django.db.models import Subquery
from django.db.transaction import atomic
from django.template.defaultfilters import capfirst
from django.utils.timezone import utc

from datahub.cleanup.query_utils import get_relations_to_delete, get_unreferenced_objects_query
from datahub.search.deletion import update_es_after_deletions

logger = getLogger(__name__)


class SimulationRollback(Exception):
    """Used to roll back deletions during a simulation."""


class BaseCleanupCommand(BaseCommand):
    """Base class for clean-up commands."""

    CONFIGS = None
    requires_migrations_checks = True

    def __repr__(self):
        """Python representation (used for parametrised tests)."""
        module_name = self.__class__.__module__.rsplit('.', maxsplit=1)[1]
        return f'{module_name}.{self.__class__.__name__}()'

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            'model_label',
            choices=self.CONFIGS,
            help='Model to clean up.',
        )
        simulation_group = parser.add_mutually_exclusive_group()
        simulation_group.add_argument(
            '--simulate',
            action='store_true',
            help='Simulates the command by performing the deletions and rolling them back.',
        )
        simulation_group.add_argument(
            '--only-print-queries',
            action='store_true',
            help='Only prints the SQL query and number of matching records. Does not delete '
                 'records or simulate deletions.',
        )

    def handle(self, *args, **options):
        """Main logic for the actual command."""
        is_simulation = options['simulate']
        only_print_queries = options['only_print_queries']
        model_name = options['model_label']

        model = apps.get_model(model_name)
        qs = self._get_query(model)

        if only_print_queries:
            self._print_queries(model, qs)
            return

        try:
            with ExitStack() as stack:
                if not is_simulation:
                    stack.enter_context(update_es_after_deletions())

                stack.enter_context(atomic())
                total_deleted, deletions_by_model = qs.delete()

                logger.info(f'{total_deleted} records deleted. Breakdown by model:')
                for deletion_model, model_deletion_count in deletions_by_model.items():
                    logger.info(f'{deletion_model}: {model_deletion_count}')

                if is_simulation:
                    logger.info(f'Rolling back deletions...')
                    raise SimulationRollback()
        except SimulationRollback:
            logger.info(f'Deletions rolled back')

    def _print_queries(self, model, qs):
        # relationships that would get deleted in cascade
        for related in get_relations_to_delete(model):
            related_model = related.related_model
            related_qs = related_model._base_manager.filter(
                **{f'{related.field.name}__in': Subquery(qs.values('pk'))}
            )
            _print_query(related_model, related_qs, related)

        # main model
        _print_query(model, qs)

    def _get_query(self, model):
        config = self.CONFIGS[model._meta.label]

        return get_unreferenced_objects_query(model).filter(
            **{f'{config.date_field}__lt': today(tzinfo=utc) - config.age_threshold}
        ).order_by(
            f'-{config.date_field}'
        )


def _print_query(model, qs, relation=None):
    model_verbose_name = capfirst(model._meta.verbose_name_plural)

    logger.info(
        ''.join((
            f'{model_verbose_name} to delete',
            f' (via {model._meta.model_name}.{relation.remote_field.name})' if relation else '',
            f': {qs.count()}'
        ))
    )

    logger.info('SQL:')
    logger.info(qs.query)
