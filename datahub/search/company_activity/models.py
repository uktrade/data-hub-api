from opensearch_dsl import Date, Keyword, Text

from datahub.search import dict_utils, fields
from datahub.search.company_activity.dict_utils import (
    activity_great_dict,
    activity_interaction_dict,
    activity_investment_dict,
    activity_order_dict,
    activity_referral_dict,
)
from datahub.search.company_activity.fields import (
    activity_great_field,
    activity_interaction_field,
    activity_investment_field,
    activity_order_field,
    activity_referral_field,
)
from datahub.search.models import BaseSearchModel


class CompanyActivity(BaseSearchModel):
    """
    OpenSearch representation of Company model and its activities.
    """

    id = Keyword()
    activity_source = Text()
    date = Date()
    company = fields.company_field()
    interaction = activity_interaction_field()
    referral = activity_referral_field()
    investment = activity_investment_field()
    order = activity_order_field()
    great_export_enquiry = activity_great_field()

    COMPUTED_MAPPINGS = {}

    MAPPINGS = {
        'interaction': activity_interaction_dict,
        'referral': activity_referral_dict,
        'company': dict_utils.company_dict,
        'investment': activity_investment_dict,
        'order': activity_order_dict,
        'great_export_enquiry': activity_great_dict,
    }

    SEARCH_FIELDS = (
        'id',
        'company.name',
        'company.name.trigram',
    )
