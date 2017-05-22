from collections import namedtuple
from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator
from raven.contrib.django.raven_compat.models import client

from datahub.company.models import Company, Contact
from datahub.core.utils import log_and_ignore_exceptions
from datahub.search.elasticsearch import bulk
from datahub.search.models import Company as ESCompany, Contact as ESContact

logger = getLogger(__name__)

ES_INDEX = settings.ES_INDEX

DataSet = namedtuple('DataSet', ('queryset', 'es_model',))


def _id_name_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'name': obj.name,
    }


def _id_type_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'type': obj.type
    }


def _contact_dict(obj):
    """Creates dictionary with selected field from supplied object."""
    return {
        'id': str(obj.id),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
    }


def _company_dict(obj):
    return {
        'id': str(obj.id),
        'company_number': obj.company_number,
    }


FieldsColumnFn = namedtuple('FieldsColumnFn', ('fields', 'fn'))

_fields_column_fn = (
    FieldsColumnFn(fields=('companies_house_data', ),
                   fn=_company_dict),
    FieldsColumnFn(fields=('account_manager', 'archived_by', 'one_list_account_owner',),
                   fn=_contact_dict),
    FieldsColumnFn(fields=('business_type', 'classification', 'employee_range',
                           'headquarter_type', 'parent', 'registered_address_country',
                           'sector', 'trading_address_country', 'turnover_range', 'uk_region',
                           'address_country', 'company', 'title',),
                   fn=_id_name_dict),
    FieldsColumnFn(fields=('interactions',),
                   fn=lambda col: [_id_type_dict(c) for c in col.all()]),
    FieldsColumnFn(fields=('contacts',),
                   fn=lambda col: [_contact_dict(c) for c in col.all()]),
    FieldsColumnFn(fields=('id',),
                   fn=lambda col: str(col)),
    FieldsColumnFn(fields=('export_to_countries', 'future_interest_countries',),
                   fn=lambda col: [_id_name_dict(c) for c in col.all()]),
)

# there is no typo in 'servicedeliverys' :(
_ignored_fields = (
    'subsidiaries', 'servicedeliverys', 'investment_projects',
    'investor_investment_projects', 'intermediate_investment_projects',
    'investee_projects', 'recipient_investment_projects', 'teams',
)


def get_dataset():
    """Returns dataset that will be synchronised with Elasticsearch."""
    return (
        DataSet(Company.objects.all(), ESCompany),
        DataSet(Contact.objects.all(), ESContact),
    )


def _model_to_dict(model, fields_column_fn=_fields_column_fn):
    """Converts model instance to a dictionary suitable for ElasticSearch."""
    result = {}
    for fcf in fields_column_fn:
        result.update({field: fcf.fn(getattr(model, field))
                       for field in fcf.fields if getattr(model, field, None)})

    fields = [field for field in model._meta.get_fields() if field.name not in _ignored_fields]

    obj = {f.name: getattr(model, f.name) for f in fields if f.name not in result}

    result.update(obj.items())

    return result


def _es_document(doc_type, source):
    """Created Elasticsearch document."""
    return {
        '_index': ES_INDEX,
        '_type': doc_type,
        '_id': source.get('id'),
        '_source': source,
    }


def _models_to_dict(models):
    """Converts models to dicts."""
    for row in models:
        yield _model_to_dict(row)


def _dict_to_es(doc_type, d):
    """Converts dicts to ElasticSearch documents."""
    for row in d:
        yield _es_document(doc_type, row)


def _batch_rows(qs, batch_size=100):
    """Yields QuerySet in chunks."""
    paginator = Paginator(qs, batch_size)
    for page in range(1, paginator.num_pages + 1):
        yield paginator.page(page).object_list


def sync_dataset(dataset, doc_type, batch_size=1):
    """Sends dataset to ElasticSearch in batches of batch_size."""
    batches = _batch_rows(dataset, batch_size=batch_size)
    for batch in batches:
        actions = list(_dict_to_es(doc_type, _models_to_dict(batch)))
        bulk(actions=actions,
             chunk_size=len(actions),
             request_timeout=300,
             raise_on_error=True,
             raise_on_exception=True,
             )


def sync_es(batch_size, dataset=None):
    """Sends data to Elasticsearch."""
    # Makes sure mappings exist in Elasticsearch.
    # Those calls are idempotent
    ESCompany.init(index=ES_INDEX)
    ESContact.init(index=ES_INDEX)

    for item in dataset:
        sync_dataset(item.queryset, item.es_model._doc_type.name, batch_size=batch_size)


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
        try:
            sync_es(batch_size=options['batch_size'], dataset=get_dataset())
        except Exception as e:
            with log_and_ignore_exceptions():
                client.captureException()

            logger.exception('Failed to sync to ES.')
            self.stderr.write(e)
