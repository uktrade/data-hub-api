from elasticsearch_dsl import Boolean, Date, Keyword, Text

from . import dict_utils as contact_dict_utils
from .. import dict_utils
from .. import dsl_utils
from ..models import BaseESModel


class Contact(BaseESModel):
    """Elasticsearch representation of Contact model."""

    id = Keyword()
    accepts_dit_email_marketing = Boolean()
    address_1 = Text()
    address_2 = Text()
    address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_county = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_postcode = Text()
    address_country = dsl_utils.nested_id_name_field()
    address_same_as_company = Boolean()
    adviser = dsl_utils.nested_contact_or_adviser_field('adviser')
    archived = Boolean()
    archived_by = dsl_utils.nested_contact_or_adviser_field('archived_by')
    archived_on = Date()
    archived_reason = Text()
    company = dsl_utils.nested_company_field('company')
    company_sector = dsl_utils.nested_sector_field()
    company_uk_region = dsl_utils.nested_id_name_field()
    contactable_by_dit = Boolean()
    contactable_by_email = Boolean()
    contactable_by_overseas_dit_partners = Boolean()
    contactable_by_phone = Boolean()
    contactable_by_uk_dit_partners = Boolean()
    created_by = dsl_utils.nested_contact_or_adviser_field('created_by', include_dit_team=True)
    created_on = Date()
    email = dsl_utils.SortableCaseInsensitiveKeywordText()
    email_alternative = Text()
    first_name = dsl_utils.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ]
    )
    job_title = dsl_utils.SortableCaseInsensitiveKeywordText()
    last_name = dsl_utils.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ])
    modified_on = Date()
    name = dsl_utils.SortableText()
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    # field is being aggregated
    name_trigram = dsl_utils.TrigramText()
    notes = dsl_utils.EnglishText()
    primary = Boolean()
    telephone_alternative = Text()
    telephone_countrycode = Keyword()
    telephone_number = Keyword()
    title = dsl_utils.nested_id_name_field()

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

        doc_type = 'contact'
