from elasticsearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import BaseESModel


class Event(BaseESModel):
    """Elasticsearch representation of Event model."""

    id = Keyword()
    address_1 = Text()
    address_2 = Text()
    address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_county = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_postcode = Text(copy_to='address_postcode_trigram')
    address_postcode_trigram = dsl_utils.TrigramText()
    address_country = dsl_utils.nested_id_name_partial_field('address_country')
    created_on = Date()
    disabled_on = Date()
    end_date = Date()
    event_type = dsl_utils.nested_id_name_field()
    lead_team = dsl_utils.nested_id_name_field()
    location_type = dsl_utils.nested_id_name_field()
    modified_on = Date()
    name = dsl_utils.SortableText(copy_to=['name_keyword', 'name_trigram'])
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    name_trigram = dsl_utils.TrigramText()
    notes = dsl_utils.EnglishText()
    organiser = dsl_utils.nested_contact_or_adviser_field('organiser')
    related_programmes = dsl_utils.nested_id_name_partial_field('related_programmes')
    service = dsl_utils.nested_id_name_field()
    start_date = Date()
    teams = dsl_utils.nested_id_name_partial_field('teams')
    uk_region = dsl_utils.nested_id_name_partial_field('uk_region')

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

        doc_type = 'event'
