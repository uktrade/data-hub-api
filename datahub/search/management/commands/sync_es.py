from collections import namedtuple
from logging import getLogger

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from django.db import models

from datahub.company.models import Company, Contact
from datahub.investment.models import InvestmentProject
from datahub.search.elasticsearch import bulk
from datahub.search.models import Company as ESCompany, \
    Contact as ESContact, \
    InvestmentProject as ESInvestmentProject

logger = getLogger(__name__)

DataSet = namedtuple('DataSet', ('queryset', 'es_model',))


def get_dataset():
    """Returns dataset that will be synchronised with Elasticsearch."""
    company_prefetch_fields = ('registered_address_country', 'business_type', 'sector', 'employee_range',
                               'turnover_range', 'account_manager', 'export_to_countries', 'future_interest_countries',
                               'trading_address_country', 'headquarter_type', 'classification',
                               'one_list_account_owner',)

    company_qs = Company.objects.prefetch_related(*company_prefetch_fields).all().order_by('pk')
    contact_qs = Contact.objects.all().order_by('pk')
    investment_project_qs = InvestmentProject.objects.all().order_by('pk')

    return (
        DataSet(company_qs, ESCompany),
        DataSet(contact_qs, ESContact),
        DataSet(investment_project_qs, ESInvestmentProject),
    )


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
            stdout.write(f'Rows processed: {rows_processed}/{total_rows} {rows_processed*100//total_rows}%')

    if stdout:
        stdout.write(f'Rows processed: {rows_processed}/{total_rows} 100%. Done!')


def sync_es(batch_size, dataset, stdout=None):
    """Sends data to Elasticsearch."""
    for item in dataset:
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
        sync_es(batch_size=options['batch_size'], dataset=get_dataset(), stdout=self.stdout)
