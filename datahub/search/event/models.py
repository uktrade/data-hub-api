from django.conf import settings
from elasticsearch_dsl import Date, DocType, String

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class Event(DocType, MapDBModelToDict):
    """Elasticsearch representation of Event model."""

    id = dsl_utils.KeywordString()
    name = String(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.CaseInsensitiveKeywordString()
    name_trigram = dsl_utils.TrigramString()
    event_type = dsl_utils.id_name_mapping()
    start_date = Date()
    end_date = Date()
    location_type = dsl_utils.id_name_mapping()
    address_1 = String()
    address_2 = String()
    address_town = dsl_utils.CaseInsensitiveKeywordString()
    address_county = dsl_utils.CaseInsensitiveKeywordString()
    address_postcode = String()
    address_country = dsl_utils.id_name_mapping()
    uk_region = dsl_utils.id_name_mapping()
    notes = dsl_utils.EnglishString()
    organiser = dsl_utils.contact_or_adviser_mapping('organiser')
    lead_team = dsl_utils.id_name_mapping()
    teams = dsl_utils.id_name_mapping()
    related_programmes = dsl_utils.id_name_mapping()

    MAPPINGS = {
        'id': str,
        'event_type': dict_utils.id_name_dict,
        'location_type': dict_utils.id_name_dict,
        'address_country': dict_utils.id_name_dict,
        'uk_region': dict_utils.id_name_dict,
        'organiser': dict_utils.contact_or_adviser_dict,
        'lead_team': dict_utils.id_name_dict,
        'teams': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'related_programmes': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
    }

    COMPUTED_MAPPINGS = {}

    IGNORED_FIELDS = (
        'created_by',
        'modified_by',
    )

    SEARCH_FIELDS = (
        'name',
        'organiser.name',
        'related_programmes.name',
        'address_country.name',
        'teams.name',
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'event'
