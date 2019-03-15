from operator import attrgetter

from elasticsearch_dsl import Boolean, Date, Double, InnerDoc, Keyword, Object, Text

from datahub.search import dict_utils, fields
from datahub.search.fields import TrigramText
from datahub.search.inner_docs import IDNameTrigram, Person
from datahub.search.models import BaseESModel


DOC_TYPE = 'interaction'


def _contact_field():
    return Object(
        properties={
            'id': Keyword(index=False),
            'first_name': Text(index=False),
            'last_name': Text(index=False),
            'name': Text(
                fields={
                    'trigram': TrigramText(),
                },
            ),
        },
    )


def _dit_participant_list(dit_participant_manager):
    return [
        {
            'adviser': dict_utils.contact_or_adviser_dict(dit_participant.adviser),
            'team': dict_utils.id_name_dict(dit_participant.team),
        }
        for dit_participant in dit_participant_manager.all()
    ]


class _DITParticipant(InnerDoc):
    adviser = Object(Person)
    team = Object(IDNameTrigram)


class Interaction(BaseESModel):
    """Elasticsearch representation of Interaction model."""

    id = Keyword()
    company = fields.company_field_with_copy_to_name_trigram('company')
    company_sector = fields.sector_field()
    communication_channel = fields.id_name_field()
    contacts = _contact_field()
    created_on = Date()
    date = Date()
    # TODO: dit_adviser is deprecated. Remove after deprecation period.
    dit_adviser = fields.contact_or_adviser_field('dit_adviser')
    dit_participants = Object(_DITParticipant)
    # TODO: dit_team is deprecated. Remove after deprecation period.
    dit_team = fields.id_name_partial_field('dit_team')
    event = fields.id_name_partial_field('event')
    investment_project = fields.id_name_field()
    investment_project_sector = fields.sector_field()
    is_event = Boolean(index=False)
    grant_amount_offered = Double()
    kind = Keyword()
    modified_on = Date()
    net_company_receipt = Double()
    notes = fields.EnglishText()
    policy_areas = fields.id_unindexed_name_field()
    policy_issue_types = fields.id_unindexed_name_field()
    service = fields.id_name_field()
    service_delivery_status = fields.id_name_field()
    subject = fields.NormalizedKeyword(
        copy_to=['subject_english'],
    )
    subject_english = fields.EnglishText()
    was_policy_feedback_provided = Boolean()

    MAPPINGS = {
        'company': dict_utils.company_dict,
        'communication_channel': dict_utils.id_name_dict,
        'contacts': dict_utils.contact_or_adviser_list_of_dicts,
        'dit_adviser': dict_utils.contact_or_adviser_dict,
        'dit_participants': _dit_participant_list,
        'dit_team': dict_utils.id_name_dict,
        'event': dict_utils.id_name_dict,
        'investment_project': dict_utils.id_name_dict,
        'policy_areas': dict_utils.id_name_list_of_dicts,
        'policy_issue_types': dict_utils.id_name_list_of_dicts,
        'service': dict_utils.id_name_dict,
        'service_delivery_status': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'investment_project_sector': dict_utils.computed_nested_sector_dict(
            'investment_project.sector',
        ),
        'is_event': attrgetter('is_event'),
    }

    SEARCH_FIELDS = (
        'id',
        'company.name',
        'company.name_trigram',
        'contacts.name',  # to find 2-letter words
        'contacts.name.trigram',
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

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
