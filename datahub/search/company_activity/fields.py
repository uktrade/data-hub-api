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
