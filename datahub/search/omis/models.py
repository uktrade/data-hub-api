from django.conf import settings
from elasticsearch_dsl import Boolean, Date, DocType, Integer, Keyword, Text

from .. import dict_utils
from .. import dsl_utils
from ..models import MapDBModelToDict


class Order(DocType, MapDBModelToDict):
    """Elasticsearch representation of Order model."""

    id = Keyword()
    reference = dsl_utils.SortableCaseInsensitiveKeywordText(copy_to='reference_trigram')
    reference_trigram = dsl_utils.TrigramText()
    status = dsl_utils.SortableCaseInsensitiveKeywordText()
    company = dsl_utils.id_name_partial_mapping('company')
    contact = dsl_utils.contact_or_adviser_partial_mapping('contact')
    created_by = dsl_utils.contact_or_adviser_mapping('created_by')
    created_on = Date()
    modified_on = Date()
    primary_market = dsl_utils.id_name_mapping()
    sector = dsl_utils.id_name_mapping()
    description = dsl_utils.EnglishText()
    contacts_not_to_approach = Text()
    delivery_date = Date()
    service_types = dsl_utils.id_name_mapping()
    contact_email = dsl_utils.SortableCaseInsensitiveKeywordText()
    contact_phone = Keyword()
    subscribers = dsl_utils.contact_or_adviser_mapping('subscribers', include_dit_team=True)
    assignees = dsl_utils.contact_or_adviser_mapping('assignees', include_dit_team=True)
    po_number = Keyword(index=False)
    discount_value = Integer(index=False)
    vat_status = Keyword(index=False)
    vat_number = Keyword(index=False)
    vat_verified = Boolean(index=False)
    net_cost = Integer(index=False)
    subtotal_cost_string = Keyword()
    subtotal_cost = Integer(copy_to=['subtotal_cost_string'])
    vat_cost = Integer(index=False)
    total_cost_string = Keyword()
    total_cost = Integer(copy_to=['total_cost_string'])
    payment_due_date = Date()
    completed_by = dsl_utils.contact_or_adviser_mapping('completed_by')
    completed_on = Date()
    cancelled_by = dsl_utils.contact_or_adviser_mapping('cancelled_by')
    cancelled_on = Date()
    cancellation_reason = dsl_utils.id_name_mapping()

    billing_contact_name = Text()
    billing_email = dsl_utils.SortableCaseInsensitiveKeywordText()
    billing_phone = dsl_utils.SortableCaseInsensitiveKeywordText()
    billing_address_1 = Text()
    billing_address_2 = Text()
    billing_address_town = dsl_utils.SortableCaseInsensitiveKeywordText()
    billing_address_county = dsl_utils.SortableCaseInsensitiveKeywordText()
    billing_address_postcode = Text()
    billing_address_country = dsl_utils.id_name_mapping()

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
        'billing_address_country': dict_utils.id_name_dict,
        'completed_by': dict_utils.contact_or_adviser_dict,
        'cancelled_by': dict_utils.contact_or_adviser_dict,
        'cancellation_reason': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'payment_due_date': lambda x: x.invoice.payment_due_date if x.invoice else None,
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
        'public_token',
        'invoice',
        'payments',
        'refunds',
        'archived_documents_url_path',
    )

    SEARCH_FIELDS = (
        'reference_trigram',
        'contact.name_trigram',
        'company.name_trigram',
        'total_cost_string',
        'subtotal_cost_string',
    )

    class Meta:
        """Default document meta data."""

        index = settings.ES_INDEX
        doc_type = 'order'
