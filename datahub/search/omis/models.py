from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Integer, String

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Order(DocType, MapDBModelToDict):
    """Elasticsearch representation of Order model."""

    id = dsl_utils.KeywordString()
    reference = dsl_utils.CaseInsensitiveKeywordString()
    status = dsl_utils.CaseInsensitiveKeywordString()
    company = dsl_utils.id_name_mapping()
    contact = dsl_utils.contact_or_adviser_mapping('contact')
    created_by = dsl_utils.contact_or_adviser_mapping('created_by')
    created_on = Date()
    modified_on = Date()
    primary_market = dsl_utils.id_name_mapping()
    sector = dsl_utils.id_name_mapping()
    description = dsl_utils.EnglishString()
    contacts_not_to_approach = String()
    delivery_date = Date()
    service_types = dsl_utils.id_name_mapping()
    contact_email = dsl_utils.CaseInsensitiveKeywordString()
    contact_phone = dsl_utils.KeywordString()
    subscribers = dsl_utils.contact_or_adviser_mapping('subscribers', include_dit_team=True)
    assignees = dsl_utils.contact_or_adviser_mapping('assignees', include_dit_team=True)
    po_number = String(index='no')
    discount_value = Integer(index='no')
    vat_status = String(index='no')
    vat_number = String(index='no')
    vat_verified = Boolean(index='no')

    MAPPINGS = {
        'id': str,
        'company': dict_utils.id_name_dict,
        'contact': dict_utils.contact_or_adviser_dict,
        'created_by': dict_utils.contact_or_adviser_dict,
        'primary_market': dict_utils.id_name_dict,
        'sector': dict_utils.id_name_dict,
        'service_types': lambda col: [dict_utils.id_name_dict(c) for c in col.all()],
        'subscribers': lambda col: [
            dict_utils.contact_or_adviser_dict(c.adviser, include_dit_team=True) for c in col.all()
        ],
        'assignees': lambda col: [
            dict_utils.contact_or_adviser_dict(c.adviser, include_dit_team=True) for c in col.all()
        ],
    }

    IGNORED_FIELDS = (
        'modified_by',
        'product_info',
        'further_info',
        'existing_agents',
        'permission_to_approach_contacts',
        'quote',
        'hourly_rate',
        'discount_label',
    )

    SEARCH_FIELDS = []

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'order'
