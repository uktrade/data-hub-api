from collections import namedtuple
from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from datahub.company.models import Company, Contact
from datahub.search.elasticsearch import bulk
from datahub.search.models import Company as ESCompany, Contact as ESContact

logger = getLogger(__name__)

ES_INDEX = settings.ES_INDEX

DataSet = namedtuple('DataSet', ('queryset', 'es_model', 'mapping',))


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


_company_mappings = {
    'companies_house_data': _company_dict,
    'account_manager': _contact_dict,
    'archived_by': _contact_dict,
    'one_list_account_owner': _contact_dict,
    'business_type': _id_name_dict,
    'classification': _id_name_dict,
    'employee_range': _id_name_dict,
    'headquarter_type': _id_name_dict,
    'parent': _id_name_dict,
    'registered_address_country': _id_name_dict,
    'sector': _id_name_dict,
    'trading_address_country': _id_name_dict,
    'turnover_range': _id_name_dict,
    'uk_region': _id_name_dict,
    'address_country': _id_name_dict,
    'contacts': lambda col: [_contact_dict(c) for c in col.all()],
    'id': str,
    'interactions': lambda col: [_id_type_dict(c) for c in col.all()],
    'export_to_countries': lambda col: [_id_name_dict(c) for c in col.all()],
    'future_interest_countries': lambda col: [_id_name_dict(c) for c in col.all()],
}

_contact_mappings = {
    'id': str,
    'title': _id_name_dict,
    'address_country': _id_name_dict,
    'advisor': _id_name_dict,
    'company': _company_dict,
    'interactions': lambda col: [_id_type_dict(c) for c in col.all()],
}

# there is no typo in 'servicedeliverys' :(
_ignored_fields = (
    'subsidiaries', 'servicedeliverys', 'investment_projects',
    'investor_investment_projects', 'intermediate_investment_projects',
    'investee_projects', 'recipient_investment_projects', 'teams',
)


def get_dataset():
    """Returns dataset that will be synchronised with Elasticsearch."""
    return (
        DataSet(Company.objects.all(), ESCompany, _company_mappings),
        DataSet(Contact.objects.all(), ESContact, _contact_mappings),
    )


def _model_to_dict(model, column_mapping):
    """Converts model instance to a dictionary suitable for ElasticSearch."""
    result = {col: fn(getattr(model, col)) for col, fn in column_mapping.items()
              if getattr(model, col, None)}

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


def _models_to_dict(models, mapping):
    """Converts models to dicts."""
    for row in models:
        yield _model_to_dict(row, mapping)


def _dict_to_es(doc_type, d):
    """Converts dicts to ElasticSearch documents."""
    for row in d:
        yield _es_document(doc_type, row)


def _batch_rows(qs, batch_size=100):
    """Yields QuerySet in chunks."""
    paginator = Paginator(qs, batch_size)
    for page in range(1, paginator.num_pages + 1):
        yield paginator.page(page).object_list


def sync_dataset(item, batch_size=1):
    """Sends dataset to ElasticSearch in batches of batch_size."""
    batches = _batch_rows(item.queryset, batch_size=batch_size)
    for batch in batches:
        actions = list(_dict_to_es(item.es_model._doc_type.name,
                                   _models_to_dict(batch, item.mapping)
                                   ))
        bulk(actions=actions,
             chunk_size=len(actions),
             request_timeout=300,
             raise_on_error=True,
             raise_on_exception=True,
             )


def sync_es(batch_size, dataset):
    """Sends data to Elasticsearch."""
    # Makes sure mappings exist in Elasticsearch.
    # Those calls are idempotent
    ESCompany.init(index=ES_INDEX)
    ESContact.init(index=ES_INDEX)

    for item in dataset:
        sync_dataset(item, batch_size=batch_size)


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
        sync_es(batch_size=options['batch_size'], dataset=get_dataset())
