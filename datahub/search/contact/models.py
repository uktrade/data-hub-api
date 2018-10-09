from elasticsearch_dsl import Boolean, Date, Keyword, Text

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.contact import dict_utils as contact_dict_utils
from datahub.search.models import BaseESModel


DOC_TYPE = 'contact'


class Contact(BaseESModel):
    """Elasticsearch representation of Contact model."""

    id = Keyword()
    accepts_dit_email_marketing = Boolean()
    address_1 = Text()
    address_2 = Text()
    address_town = fields.SortableCaseInsensitiveKeywordText()
    address_county = fields.SortableCaseInsensitiveKeywordText()
    address_postcode = Text()
    address_country = fields.nested_id_name_field()
    address_same_as_company = Boolean()
    adviser = fields.nested_contact_or_adviser_field('adviser')
    archived = Boolean()
    archived_by = fields.nested_contact_or_adviser_field('archived_by')
    archived_on = Date()
    archived_reason = Text()
    company = fields.nested_company_field('company')
    company_sector = fields.nested_sector_field()
    company_uk_region = fields.nested_id_name_field()
    created_by = fields.nested_contact_or_adviser_field('created_by', include_dit_team=True)
    created_on = Date()
    email = fields.SortableCaseInsensitiveKeywordText()
    email_alternative = Text()
    first_name = fields.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ],
    )
    job_title = fields.SortableCaseInsensitiveKeywordText()
    last_name = fields.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ],
    )
    modified_on = Date()
    name = fields.SortableText()
    name_keyword = fields.SortableCaseInsensitiveKeywordText()
    # field is being aggregated
    name_trigram = fields.TrigramText()
    notes = fields.EnglishText()
    primary = Boolean()
    telephone_alternative = Text()
    telephone_countrycode = Keyword()
    telephone_number = Keyword()
    title = fields.nested_id_name_field()

    MAPPINGS = {
        'id': str,
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
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'company_uk_region': dict_utils.computed_nested_id_name_dict('company.uk_region'),
    }

    SEARCH_FIELDS = (
        'name',
        'name_trigram',
        'email',
        'email_alternative',
        'company.name',
        'company.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
