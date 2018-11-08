from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel


DOC_TYPE = 'event'


class Event(BaseESModel):
    """Elasticsearch representation of Event model."""

    id = Keyword()
    address_1 = Text()
    address_2 = Text()
    address_town = fields.SortableCaseInsensitiveKeywordText()
    address_county = fields.SortableCaseInsensitiveKeywordText()
    address_postcode = Text(copy_to='address_postcode_trigram')
    address_postcode_trigram = fields.TrigramText()
    address_country = fields.nested_id_name_partial_field('address_country')
    created_on = Date()
    disabled_on = Date()
    end_date = Date()
    event_type = fields.nested_id_name_field()
    lead_team = fields.nested_id_name_field()
    location_type = fields.nested_id_name_field()
    modified_on = Date()
    name = fields.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = fields.SortableCaseInsensitiveKeywordText()
    name_trigram = fields.TrigramText()
    notes = fields.EnglishText()
    organiser = fields.nested_contact_or_adviser_field('organiser')
    related_programmes = fields.nested_id_name_partial_field('related_programmes')
    service = fields.nested_id_name_field()
    start_date = Date()
    teams = fields.nested_id_name_partial_field('teams')
    uk_region = fields.nested_id_name_partial_field('uk_region')

    MAPPINGS = {
        'id': str,
        'address_country': dict_utils.id_name_dict,
        'event_type': dict_utils.id_name_dict,
        'lead_team': dict_utils.id_name_dict,
        'location_type': dict_utils.id_name_dict,
        'organiser': dict_utils.contact_or_adviser_dict,
        'related_programmes': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'service': dict_utils.id_name_dict,
        'teams': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'uk_region': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {}

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'address_country.name_trigram',
        'address_postcode_trigram',
        'uk_region.name_trigram',
        'organiser.name_trigram',
        'teams.name',
        'teams.name_trigram',
        'related_programmes.name',
        'related_programmes.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
