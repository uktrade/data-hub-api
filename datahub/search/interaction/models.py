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


def _export_country_field():
    return Object(
        properties={
            'id': Keyword(index=False),
            'country': Object(
                properties={
                    'id': Keyword(),
                    'name': Text(index=False),
                }),
            'status': Object(
                properties={
                    'type': Keyword(),
                }),
        },
    )


def _export_countries_list(export_countries):
    return [
        {
            'country': dict_utils.id_name_dict(export_country.country),
            'status': export_country.status,
        }
        for export_country in export_countries.all()
    ]


class _DITParticipant(InnerDoc):
    adviser = Object(Person)
    team = Object(IDNameTrigram)


class Interaction(BaseESModel):
    """Elasticsearch representation of Interaction model."""

    id = Keyword()
    company = fields.company_field()
    company_sector = fields.sector_field()
    company_one_list_group_tier = fields.id_unindexed_name_field()
    communication_channel = fields.id_unindexed_name_field()
    contacts = _contact_field()
    export_countries = _export_country_field()
    created_on = Date()
    date = Date()
    dit_participants = Object(_DITParticipant)
    event = fields.id_name_partial_field()
    investment_project = fields.id_unindexed_name_field()
    investment_project_sector = fields.sector_field()
    is_event = Boolean(index=False)
    grant_amount_offered = Double(index=False)
    kind = Keyword()
    modified_on = Date()
    net_company_receipt = Double(index=False)
    notes = fields.Text(index=False)
    policy_areas = fields.id_unindexed_name_field()
    policy_issue_types = fields.id_unindexed_name_field()
    service = fields.id_unindexed_name_field()
    service_delivery_status = fields.id_unindexed_name_field()
    subject = fields.NormalizedKeyword(
        fields={
            'english': fields.EnglishText(),
        },
    )
    was_policy_feedback_provided = Boolean()
    were_countries_discussed = Boolean()

    MAPPINGS = {
        'company': dict_utils.company_dict,
        'communication_channel': dict_utils.id_name_dict,
        'contacts': dict_utils.contact_or_adviser_list_of_dicts,
        'dit_participants': _dit_participant_list,
        'export_countries': _export_countries_list,
        'event': dict_utils.id_name_dict,
        'investment_project': dict_utils.id_name_dict,
        'policy_areas': dict_utils.id_name_list_of_dicts,
        'policy_issue_types': dict_utils.id_name_list_of_dicts,
        'service': dict_utils.id_name_dict,
        'service_delivery_status': dict_utils.id_name_dict,
    }

    COMPUTED_MAPPINGS = {
        'company_sector': dict_utils.computed_nested_sector_dict('company.sector'),
        'company_one_list_group_tier': lambda obj: dict_utils.id_name_dict(
            obj.company.get_one_list_group_tier() if obj.company else None,
        ),
        'investment_project_sector': dict_utils.computed_nested_sector_dict(
            'investment_project.sector',
        ),
        'is_event': attrgetter('is_event'),
    }

    SEARCH_FIELDS = (
        'id',
        'company.name',
        'company.name.trigram',
        'contacts.name',  # to find 2-letter words
        'contacts.name.trigram',
        'event.name',
        'event.name.trigram',
        'subject.english',
        'dit_participants.adviser.name',
        'dit_participants.adviser.name.trigram',
        'dit_participants.team.name',
        'dit_participants.team.name.trigram',
    )

    class Meta:
        """Default document meta data."""

        doc_type = DOC_TYPE

    class Index:
        doc_type = DOC_TYPE
