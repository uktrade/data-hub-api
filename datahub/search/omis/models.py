from django.conf import settings
from elasticsearch_dsl import Date, DocType, String

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Order(DocType, MapDBModelToDict):
    """Elasticsearch representation of Order model."""

    id = String(index='not_analyzed')
    reference = String(analyzer='lowercase_keyword_analyzer')
    company = dsl_utils.id_name_mapping()
    contact = dsl_utils.contact_mapping('contact')
    created_by = dsl_utils.contact_mapping('created_by')
    created_on = Date()
    primary_market = dsl_utils.id_name_mapping()
    sector = dsl_utils.id_name_mapping()
    description = String()
    contacts_not_to_approach = String()
    delivery_date = Date()
    service_types = dsl_utils.id_name_mapping()
    contact_email = dsl_utils.CaseInsensitiveKeywordString()
    contact_phone = dsl_utils.KeywordString()
    subscribers = dsl_utils.contact_mapping('subscribers', include_dit_team=True)
    assignees = dsl_utils.contact_mapping('assignees', include_dit_team=True)

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
        'modified_on',
        'product_info',
        'further_info',
        'existing_agents',
        'permission_to_approach_contacts',
    )

    SEARCH_FIELDS = []

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'order'
