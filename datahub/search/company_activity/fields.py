from opensearch_dsl import Date, Keyword, Object, Text

from datahub.search import fields
from datahub.search.interaction.models import _DITParticipant


def activity_interaction_field():
    return Object(
        properties={
            'id': Keyword(),
            'subject': Text(index=False),
            'service': fields.id_name_partial_field(),
            'kind': Text(index=False),
            'date': Date(),
            'dit_participants': Object(_DITParticipant),
            'communication_channel': fields.id_unindexed_name_field(),
            'contacts': fields.contact_or_adviser_field(),
        },
    )


def activity_referral_field():
    return Object(
        properties={
            'id': Keyword(),
            'subject': Text(index=False),
            'notes': Text(index=False),
            'status': Text(index=False),
            'completed_on': Date(),
            'created_on': Date(),
            'created_by': fields.contact_or_adviser_field(),
            'recipient': fields.contact_or_adviser_field(),
            'contact': fields.contact_or_adviser_field(),
        },
    )


def activity_investment_field():
    return Object(
        properties={
            'id': Keyword(),
            'name': Text(index=False),
            'investment_type': fields.id_name_field(),
            'estimated_land_date': Date(),
            'total_investment': Text(index=False),
            'foreign_equity_investment': Text(index=False),
            'gross_value_added': Text(index=False),
            'number_new_jobs': Text(index=False),
            'created_by': fields.contact_or_adviser_field(),
            'client_contacts': fields.contact_job_field(),
        },
    )


def activity_order_field():
    return Object(
        properties={
            'id': Keyword(),
            'created_on': Date(),
            'reference': Text(index=False),
            'primary_market': fields.country_field(),
            'uk_region': fields.area_field(),
            'contact': fields.contact_job_field(),
            'created_by': fields.contact_or_adviser_field(),
        },
    )


def activity_great_field():
    return Object(
        properties={
            'id': Keyword(),
            'form_created_at': Date(),
            'meta_full_name': Text(index=False),
            'meta_email_address': Text(index=False),
            'contact': fields.contact_job_field(),
            'meta_subject': Text(index=False),
            'data_enquiry': Text(index=False),
        },
    )
