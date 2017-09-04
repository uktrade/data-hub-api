from django.conf import settings
from elasticsearch_dsl import Date, DocType, Keyword

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class Interaction(DocType, MapDBModelToDict):
    """Elasticsearch representation of Interaction model."""

    id = Keyword()
    kind = Keyword()
    date = Date()
    company = dsl_utils.id_name_partial_mapping('company')
    contact = dsl_utils.contact_or_adviser_partial_mapping('contact')
    event = dsl_utils.id_name_partial_mapping('event')
    service = dsl_utils.id_name_mapping()
    subject = dsl_utils.EnglishString(fielddata=True)
    dit_adviser = dsl_utils.contact_or_adviser_partial_mapping('dit_adviser')
    notes = dsl_utils.EnglishString()
    dit_team = dsl_utils.id_name_mapping()
    communication_channel = dsl_utils.id_name_mapping()
    investment_project = dsl_utils.id_name_mapping()
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
    }

    COMPUTED_MAPPINGS = {}

    IGNORED_FIELDS = (
        'created_by',
        'modified_by',
    )

    SEARCH_FIELDS = [
        'subject',
        'company.name',
        'contact.name',
        'dit_team.name',
        'notes'
    ]

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'interaction'
