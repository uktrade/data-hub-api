from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, String

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Contact(DocType, MapDBModelToDict):
    """Elasticsearch representation of Contact model."""

    id = String(index='not_analyzed')
    archived = Boolean()
    archived_on = Date()
    archived_reason = String()
    created_on = Date()
    modified_on = Date()
    name = String()
    name_keyword = dsl_utils.CaseInsensitiveKeywordString()
    name_trigram = dsl_utils.TrigramString()
    title = dsl_utils._id_name_mapping()
    first_name = String(copy_to=['name', 'name_keyword', 'name_trigram'])
    last_name = String(copy_to=['name', 'name_keyword', 'name_trigram'])
    primary = Boolean()
    telephone_countrycode = dsl_utils.KeywordString()
    telephone_number = dsl_utils.KeywordString()
    email = dsl_utils.CaseInsensitiveKeywordString()
    address_same_as_company = Boolean()
    address_1 = String()
    address_2 = String()
    address_town = dsl_utils.CaseInsensitiveKeywordString()
    address_county = dsl_utils.CaseInsensitiveKeywordString()
    address_postcode = String()
    telephone_alternative = String()
    email_alternative = String()
    notes = String()
    job_title = dsl_utils.CaseInsensitiveKeywordString()
    contactable_by_dit = Boolean()
    contactable_by_dit_partners = Boolean()
    contactable_by_email = Boolean()
    contactable_by_phone = Boolean()
    address_country = dsl_utils._id_name_mapping()
    adviser = dsl_utils._contact_mapping('adviser')
    archived_by = dsl_utils._contact_mapping('archived_by')
    company = dsl_utils._id_name_mapping()
    company_sector = dsl_utils._id_name_mapping()

    MAPPINGS = {
        'id': str,
        'title': dict_utils._id_name_dict,
        'address_country': dict_utils._id_name_dict,
        'adviser': dict_utils._contact_dict,
        'company': dict_utils._id_name_dict,
        'archived_by': dict_utils._contact_dict,
    }

    COMPUTED_MAPPINGS = {
        'company_sector': dict_utils._computed_nested_id_name_dict('company.sector'),
    }

    IGNORED_FIELDS = (
        'created_by',
        'interactions',
        'investment_projects',
        'modified_by',
        'orders',
        'servicedeliverys'
    )

    SEARCH_FIELDS = [
        'address_1',
        'address_2',
        'address_country.name',
        'address_county',
        'address_town',
        'company.name',
        'email',
        'notes'
    ]

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'contact'
