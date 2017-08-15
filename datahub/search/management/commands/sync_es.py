from logging import getLogger

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db import models

from datahub.search.elasticsearch import bulk

from ...apps import get_search_apps

logger = getLogger(__name__)


def get_datasets():
    """Returns datasets that will be synchronised with Elasticsearch."""
    return [
        search_app.get_dataset()
        for search_app in get_search_apps()
    ]


def _batch_rows(qs, batch_size=100):
    """Yields QuerySet in chunks."""
    paginator = Paginator(qs, batch_size)
    for page in range(1, paginator.num_pages + 1):
        yield paginator.page(page).object_list


def sync_dataset(item, batch_size=1, stdout=None):
    """Sends dataset to ElasticSearch in batches of batch_size."""
    rows_processed = 0
    total_rows = item.queryset.count() \
        if isinstance(item.queryset, models.query.QuerySet) else len(item.queryset)
    batches_processed = 0
    batches = _batch_rows(item.queryset, batch_size=batch_size)
    for batch in batches:
        actions = list(item.es_model.dbmodels_to_es_documents(batch))
        num_actions = len(actions)
        bulk(actions=actions,
             chunk_size=num_actions,
             request_timeout=300,
             raise_on_error=True,
             raise_on_exception=True,
             )

        rows_processed += num_actions
        batches_processed += 1
        if stdout and batches_processed % 100 == 0:
            stdout.write(f'Rows processed: {rows_processed}/{total_rows} '
                         f'{rows_processed*100//total_rows}%')

    if stdout:
        stdout.write(f'Rows processed: {rows_processed}/{total_rows} 100%. Done!')


def sync_es(batch_size, datasets, stdout=None):
    """Sends data to Elasticsearch."""
    for item in datasets:
        sync_dataset(item, batch_size=batch_size, stdout=stdout)


class Command(BaseCommand):
    """Elasticsearch sync command."""

    def add_arguments(self, parser):
        """Handle arguments."""
        parser.add_argument(
            '--batch_size',
            dest='batch_size',
            default=100,
            help='Batch size - number of rows processed at a time',
        )

    def handle(self, *args, **options):
        """Handle."""
        sync_es(batch_size=options['batch_size'], datasets=get_datasets(), stdout=self.stdout)
