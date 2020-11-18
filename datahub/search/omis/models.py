from elasticsearch_dsl import Boolean, Date, Integer, Keyword, Text

from datahub.search import dict_utils
from datahub.search import fields
from datahub.search.models import BaseESModel


class Order(BaseESModel):
    """Elasticsearch representation of Order model."""

    id = Keyword()
    reference = fields.NormalizedKeyword(
        fields={
            'trigram': fields.TrigramText(),
        },
    )
    status = fields.NormalizedKeyword()
    company = fields.company_field()
    contact = fields.contact_or_adviser_field()
    created_by = fields.contact_or_adviser_field(include_dit_team=True)
    created_on = Date()
    modified_on = Date()
    primary_market = fields.id_name_field()
    sector = fields.sector_field()
    uk_region = fields.id_name_field()
    description = fields.EnglishText()
    contacts_not_to_approach = Text()
    further_info = Text()
    existing_agents = Text(index=False)
    delivery_date = Date()
    service_types = fields.id_name_field()
    contact_email = fields.NormalizedKeyword()
    contact_phone = Keyword()
    subscribers = fields.contact_or_adviser_field(include_dit_team=True)
    assignees = fields.contact_or_adviser_field(include_dit_team=True)
    po_number = Keyword(index=False)
    discount_value = Integer(index=False)
    vat_status = Keyword(index=False)
    vat_number = Keyword(index=False)
    vat_verified = Boolean(index=False)
    net_cost = Integer(index=False)
    subtotal_cost = Integer(
        fields={
            'keyword': Keyword(),
        },
    )
    vat_cost = Integer(index=False)
    total_cost = Integer(
        fields={
            'keyword': Keyword(),
        },
    )
    payment_due_date = Date()
    paid_on = Date()
    completed_by = fields.contact_or_adviser_field()
    completed_on = Date()
    cancelled_by = fields.contact_or_adviser_field()
    cancelled_on = Date()
    cancellation_reason = fields.id_name_field()

    billing_company_name = Text()
    billing_contact_name = Text()
    billing_email = fields.NormalizedKeyword()
    billing_phone = fields.NormalizedKeyword()
    billing_address_1 = Text()
    billing_address_2 = Text()
    billing_address_town = fields.NormalizedKeyword()
    billing_address_county = fields.NormalizedKeyword()
    billing_address_postcode = Text()
    billing_address_country = fields.id_name_field()

    MAPPINGS = {
        'company': dict_utils.company_dict,
        'contact': dict_utils.contact_or_adviser_dict,
        'created_by': dict_utils.adviser_dict_with_team,
        'primary_market': dict_utils.id_name_dict,
        'sector': dict_utils.sector_dict,
        'uk_region': dict_utils.id_name_dict,
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

    SEARCH_FIELDS = (
        'id',
        'reference.trigram',
        'company.name',
        'company.name.trigram',
        'contact.name',
        'contact.name.trigram',
        'total_cost.keyword',
        'subtotal_cost.keyword',
    )
