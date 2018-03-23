from operator import attrgetter

from elasticsearch_dsl import Boolean, Date, DocType, Double, Keyword

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class Interaction(DocType, MapDBModelToDict):
    """Elasticsearch representation of Interaction model."""

    id = Keyword()
    kind = Keyword()
    date = Date()
    company = dsl_utils.id_name_partial_mapping('company')
    company_sector = dsl_utils.sector_mapping()
    contact = dsl_utils.contact_or_adviser_partial_mapping('contact')
    is_event = Boolean()
    event = dsl_utils.id_name_partial_mapping('event')
    service = dsl_utils.id_name_mapping()
    subject = dsl_utils.SortableCaseInsensitiveKeywordText(
        copy_to=['subject_english']
    )
    subject_english = dsl_utils.EnglishText()
    dit_adviser = dsl_utils.contact_or_adviser_partial_mapping('dit_adviser')
    notes = dsl_utils.EnglishText()
    dit_team = dsl_utils.id_name_partial_mapping('dit_team')
    communication_channel = dsl_utils.id_name_mapping()
    investment_project = dsl_utils.id_name_mapping()
    investment_project_sector = dsl_utils.sector_mapping()
    service_delivery_status = dsl_utils.id_name_mapping()
    grant_amount_offered = Double()
    net_company_receipt = Double()
    created_on = Date()
    modified_on = Date()

    MAPPINGS = {
        'id': str,
        'company': dict_utils.id_name_dict,
        'contact': dict_utils.contact_or_adviser_dict,
        'event': dict_utils.id_name_dict,
        'service': dict_utils.id_name_dict,
        'dit_adviser': dict_utils.contact_or_adviser_dict,
        'dit_team': dict_utils.id_name_dict,
        'communication_channel': dict_utils.id_name_dict,
        'investment_project': dict_utils.id_name_dict,
        'service_delivery_status': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'is_event': attrgetter('is_event'),
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'investment_project_sector': dict_utils.computed_nested_sector_dict(
            'investment_project.sector'
        ),
    }

    IGNORED_FIELDS = (
        'created_by',
        'modified_by',
        'archived_documents_url_path',
    )

    SEARCH_FIELDS = (
        'company.name',
        'company.name_trigram',
        'contact.name',
        'contact.name_trigram',
        'event.name',
        'event.name_trigram',
        'subject_english',
        'dit_adviser.name',
        'dit_adviser.name_trigram',
        'dit_team.name',
        'dit_team.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'interaction'
