from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.models import BaseESModel


class Event(BaseESModel):
    """Elasticsearch representation of Event model."""

    id = Keyword()
    address_1 = Text()
    address_2 = Text()
    address_town = fields.NormalizedKeyword()
    address_county = fields.NormalizedKeyword()
    address_postcode = fields.TextWithTrigram()
    address_country = fields.id_name_partial_field()
    created_on = Date()
    disabled_on = Date()
    end_date = Date()
    event_type = fields.id_name_field()
    lead_team = fields.id_name_field()
    location_type = fields.id_name_field()
    modified_on = Date()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    notes = fields.EnglishText()
    organiser = fields.contact_or_adviser_field()
    related_programmes = fields.id_name_partial_field()
    service = fields.id_name_field()
    start_date = Date()
    teams = fields.id_name_partial_field()
    uk_region = fields.id_name_partial_field()

    MAPPINGS = {
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
        'id',
        'name',
        'name.trigram',
        'address_country.name.trigram',
        'address_postcode.trigram',
        'uk_region.name.trigram',
        'organiser.name.trigram',
        'teams.name',
        'teams.name.trigram',
        'related_programmes.name',
        'related_programmes.name.trigram',
    )
