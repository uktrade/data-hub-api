from opensearch_dsl import Boolean, Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.contact import dict_utils as contact_dict_utils
from datahub.search.models import BaseSearchModel


class Contact(BaseSearchModel):
    """OpenSearch representation of Contact model."""

    id = Keyword()
    address_1 = Text()
    address_2 = Text()
    address_town = fields.NormalizedKeyword()
    address_county = fields.NormalizedKeyword()
    address_postcode = Text()
    address_country = fields.id_name_field()
    address_area = fields.id_name_field()
    address_same_as_company = Boolean()
    adviser = fields.contact_or_adviser_field()
    archived = Boolean()
    archived_by = fields.contact_or_adviser_field()
    archived_on = Date()
    archived_reason = Text()
    company = fields.company_field()
    company_sector = fields.sector_field()
    company_uk_region = fields.id_name_field()
    created_by = fields.contact_or_adviser_field(include_dit_team=True)
    created_on = Date()
    email = fields.NormalizedKeyword()
    first_name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
        },
    )
    job_title = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    last_name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
        },
    )
    modified_on = Date()
    name = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    name_with_title = Text(
        fields={
            'keyword': fields.NormalizedKeyword(),
            'trigram': fields.TrigramText(),
        },
    )
    notes = fields.EnglishText()
    primary = Boolean()
    full_telephone_number = Keyword()
    title = fields.id_name_field()
    valid_email = Boolean()
    consent_data_last_modified = Date()

    MAPPINGS = {
        'adviser': dict_utils.contact_or_adviser_dict,
        'archived_by': dict_utils.contact_or_adviser_dict,
        'company': dict_utils.company_dict,
        'created_by': dict_utils.adviser_dict_with_team,
        'title': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'address_1': contact_dict_utils.computed_address_field('address_1'),
        'address_2': contact_dict_utils.computed_address_field('address_2'),
        'address_town': contact_dict_utils.computed_address_field('address_town'),
        'address_county': contact_dict_utils.computed_address_field('address_county'),
        'address_postcode': contact_dict_utils.computed_address_field('address_postcode'),
        'address_country': contact_dict_utils.computed_address_field('address_country'),
        'address_area': contact_dict_utils.computed_address_field('address_area'),
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'company_uk_region': dict_utils.computed_nested_id_name_dict('company.uk_region'),
    }

    SEARCH_FIELDS = (
        'id',
        'name',
        'name.trigram',
        'name_with_title',
        'name_with_title.trigram',
        'email',
        'company.name',
        'company.name.trigram',
        'job_title',
        'job_title.trigram',
        'full_telephone_number',
    )
