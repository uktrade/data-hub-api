from elasticsearch_dsl import Boolean, Date, DocType, Keyword, Text

from . import dict_utils as contact_dict_utils
from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Contact(DocType, MapDBModelToDict):
    """Elasticsearch representation of Contact model."""

    id = Keyword()
    archived = Boolean()
    archived_on = Date()
    archived_reason = Text()
    created_on = Date()
    modified_on = Date()
    name = dsl_utils.SortableText()
    name_keyword = dsl_utils.SortableCaseInsensitiveKeywordText()
    # field is being aggregated
    name_trigram = dsl_utils.TrigramText()
    title = dsl_utils.id_name_mapping()
    first_name = dsl_utils.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ]
    )
    last_name = dsl_utils.SortableText(
        copy_to=[
            'name',
            'name_keyword',
            'name_trigram',
        ])
    primary = Boolean()
    telephone_countrycode = Keyword()
    telephone_number = Keyword()
    email = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_same_as_company = Boolean()
    address_1 = Text()
    address_2 = Text()
    address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_county = dsl_utils.SortableCaseInsensitiveKeywordText()
    address_postcode = Text()
    telephone_alternative = Text()
    email_alternative = Text()
    notes = dsl_utils.EnglishText()
    job_title = dsl_utils.SortableCaseInsensitiveKeywordText()
    contactable_by_dit = Boolean()
    contactable_by_uk_dit_partners = Boolean()
    contactable_by_overseas_dit_partners = Boolean()
    accepts_dit_email_marketing = Boolean()
    contactable_by_email = Boolean()
    contactable_by_phone = Boolean()
    address_country = dsl_utils.id_name_mapping()
    adviser = dsl_utils.contact_or_adviser_mapping('adviser')
    archived_by = dsl_utils.contact_or_adviser_mapping('archived_by')
    company = dsl_utils.id_name_partial_mapping('company')
    company_sector = dsl_utils.id_name_mapping()
    company_uk_region = dsl_utils.id_name_mapping()
    created_by = dsl_utils.contact_or_adviser_mapping('created_by', include_dit_team=True)

    MAPPINGS = {
        'id': str,
        'title': dict_utils.id_name_dict,
        'adviser': dict_utils.contact_or_adviser_dict,
        'company': dict_utils.id_name_dict,
        'archived_by': dict_utils.contact_or_adviser_dict,
        'created_by': dict_utils.adviser_dict_with_team,
    }

    COMPUTED_MAPPINGS = {
        'company_sector': dict_utils.computed_nested_id_name_dict('company.sector'),
        'company_uk_region': dict_utils.computed_nested_id_name_dict('company.uk_region'),
        'address_1': contact_dict_utils.computed_address_field('address_1'),
        'address_2': contact_dict_utils.computed_address_field('address_2'),
        'address_town': contact_dict_utils.computed_address_field('address_town'),
        'address_county': contact_dict_utils.computed_address_field('address_county'),
        'address_postcode': contact_dict_utils.computed_address_field('address_postcode'),
        'address_country': contact_dict_utils.computed_address_field('address_country'),
    }

    IGNORED_FIELDS = (
        'interactions',
        'investment_projects',
        'modified_by',
        'orders',
        'archived_documents_url_path',
    )

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
