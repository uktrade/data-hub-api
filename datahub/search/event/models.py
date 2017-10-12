from django.conf import settings
from elasticsearch_dsl import Date, DocType, Keyword, Text

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import MapDBModelToDict


class Event(DocType, MapDBModelToDict):
    """Elasticsearch representation of Event model."""

    id = Keyword()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    event_type = dsl_utils.id_name_mapping()
    start_date = Date()
    end_date = Date()
    location_type = dsl_utils.id_name_mapping()
    address_1 = Text()
    address_2 = Text()
    address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_county = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_postcode = Text()
    address_country = dsl_utils.id_name_mapping()
    uk_region = dsl_utils.id_name_mapping()
    notes = dsl_utils.EnglishText()
    organiser = dsl_utils.contact_or_adviser_partial_mapping('organiser')
    lead_team = dsl_utils.id_name_mapping()
    teams = dsl_utils.id_name_mapping()
    related_programmes = dsl_utils.id_name_mapping()
    service = dsl_utils.id_name_mapping()
    disabled_on = Date()

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
        'service': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {}

    IGNORED_FIELDS = (
        'created_by',
        'modified_by',
        'interactions',
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
