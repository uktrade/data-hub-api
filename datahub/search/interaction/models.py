from operator import attrgetter

from elasticsearch_dsl import Boolean, Date, Double, Keyword

from datahub.search import dict_utils, dsl_utils
from datahub.search.models import BaseESModel


class Interaction(BaseESModel):
    """Elasticsearch representation of Interaction model."""

    id = Keyword()
    company = dsl_utils.nested_company_field('company')
    company_sector = dsl_utils.nested_sector_field()
    communication_channel = dsl_utils.nested_id_name_field()
    contact = dsl_utils.nested_contact_or_adviser_field('contact')
    created_on = Date()
    date = Date()
    dit_adviser = dsl_utils.nested_contact_or_adviser_field('dit_adviser')
    dit_team = dsl_utils.nested_id_name_partial_field('dit_team')
    event = dsl_utils.nested_id_name_partial_field('event')
    investment_project = dsl_utils.nested_id_name_field()
    investment_project_sector = dsl_utils.nested_sector_field()
    is_event = Boolean()
    grant_amount_offered = Double()
    kind = Keyword()
    modified_on = Date()
    net_company_receipt = Double()
    notes = dsl_utils.EnglishText()
    service = dsl_utils.nested_id_name_field()
    service_delivery_status = dsl_utils.nested_id_name_field()
    subject = dsl_utils.SortableCaseInsensitiveKeywordText(
        copy_to=['subject_english']
    )
    subject_english = dsl_utils.EnglishText()

    MAPPINGS = {
        'id': str,
        'company': dict_utils.company_dict,
        'communication_channel': dict_utils.id_name_dict,
        'contact': dict_utils.contact_or_adviser_dict,
        'dit_adviser': dict_utils.contact_or_adviser_dict,
        'dit_team': dict_utils.id_name_dict,
        'event': dict_utils.id_name_dict,
        'investment_project': dict_utils.id_name_dict,
        'service': dict_utils.id_name_dict,
        'service_delivery_status': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'investment_project_sector': dict_utils.computed_nested_sector_dict(
            'investment_project.sector'
        ),
        'is_event': attrgetter('is_event'),
    }

    SEARCH_FIELDS = (
        'company.name',
        'company.name_trigram',
        'contact.name',
        'contact.name_trigram',
        'event.name',
        'event.name_trigram',
        'subject_english',
        'dit_adviser.name',
        'dit_adviser.name_trigram',
        'dit_team.name',
        'dit_team.name_trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = 'interaction'
