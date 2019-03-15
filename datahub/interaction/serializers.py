from operator import not_

from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import is_blank, is_not_blank
from datahub.core.validators import (
    EqualsRule,
    OperatorRule,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.event.models import Event
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionDITParticipant,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.permissions import HasAssociatedInvestmentProjectValidator
from datahub.interaction.validators import ContactsBelongToCompanyValidator
from datahub.investment.project.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Service, Team


class InteractionDITParticipantSerializer(serializers.ModelSerializer):
    """
    Interaction DIT participant serialiser.

    Used within InteractionSerializer.
    """

    adviser = NestedAdviserField()
    team = NestedRelatedField(Team)

    class Meta:
        model = InteractionDITParticipant
        fields = ('adviser', 'team')


class InteractionSerializer(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    default_error_messages = {
        'invalid_for_non_service_delivery': ugettext_lazy(
            'This field is only valid for service deliveries.',
        ),
        'invalid_for_service_delivery': ugettext_lazy(
            'This field is not valid for service deliveries.',
        ),
        'invalid_for_non_interaction': ugettext_lazy(
            'This field is only valid for interactions.',
        ),
        'invalid_for_non_interaction_or_service_delivery': ugettext_lazy(
            'This value is only valid for interactions and service deliveries.',
        ),
        'invalid_for_non_event': ugettext_lazy(
            'This field is only valid for event service deliveries.',
        ),
        'invalid_when_no_policy_feedback': ugettext_lazy(
            'This field is only valid when policy feedback has been provided.',
        ),
        'too_many_contacts_for_event_service_delivery': ugettext_lazy(
            'Only one contact can be provided for event service deliveries.',
        ),
    }

    company = NestedRelatedField(Company)
    contacts = NestedRelatedField(
        Contact,
        many=True,
        allow_empty=False,
        extra_fields=(
            'name',
            'first_name',
            'last_name',
            'job_title',
        ),
    )
    created_by = NestedAdviserField(read_only=True)
    dit_adviser = NestedAdviserField()
    dit_participants = InteractionDITParticipantSerializer(many=True, read_only=True)
    dit_team = NestedRelatedField(Team)
    communication_channel = NestedRelatedField(
        CommunicationChannel, required=False, allow_null=True,
    )
    is_event = serializers.BooleanField(required=False, allow_null=True)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedInvestmentProjectField(required=False, allow_null=True)
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service)
    service_delivery_status = NestedRelatedField(
        ServiceDeliveryStatus, required=False, allow_null=True,
    )
    policy_areas = NestedRelatedField(PolicyArea, many=True, required=False, allow_empty=True)
    policy_issue_types = NestedRelatedField(
        PolicyIssueType,
        allow_empty=True,
        many=True,
        required=False,
    )

    def validate(self, data):
        """
        Removes the semi-virtual field is_event from the data.

        This is removed because the value is not stored; it is instead inferred from contents
        of the the event field during serialisation.
        """
        if 'is_event' in data:
            del data['is_event']

        # Copies the first contact specific to contact (for backwards compatibility with
        # anything consuming the database)
        # TODO Remove following deprecation period.
        if 'contacts' in data:
            contacts = data['contacts']
            data['contact'] = contacts[0] if contacts else None

        return data

    @atomic
    def create(self, validated_data):
        """
        Create an interaction.

        Overridden so that dit_adviser and dit_team can be copied to dit_participants.

        TODO: Remove once dit_adviser and dit_team have been fully replaced by dit_participants.
        """
        interaction = super().create(validated_data)

        # These fields are required, so we can assume they are present
        dit_adviser = validated_data['dit_adviser']
        dit_team = validated_data['dit_team']

        dit_participant = InteractionDITParticipant(
            interaction=interaction,
            adviser=dit_adviser,
            team=dit_team,
        )
        dit_participant.save()

        return interaction

    @atomic
    def update(self, instance, validated_data):
        """
        Create an interaction.

        Overridden so that dit_adviser and dit_team can be copied to dit_participants.

        TODO: Remove once dit_adviser and dit_team have been fully replaced by dit_participants.
        """
        interaction = super().update(instance, validated_data)

        InteractionDITParticipant.objects.update_or_create(
            interaction=interaction,
            defaults={
                'adviser': interaction.dit_adviser,
                'team': interaction.dit_team,
            },
        )

        return interaction

    class Meta:
        model = Interaction
        extra_kwargs = {
            # Date is a datetime in the model, but only the date component is used
            # (at present). Setting the formats as below effectively makes the field
            # behave like a date field without changing the schema and breaking the
            # v1 API.
            'date': {'format': '%Y-%m-%d', 'input_formats': ['%Y-%m-%d']},
            'grant_amount_offered': {'min_value': 0},
            'net_company_receipt': {'min_value': 0},
        }
        fields = (
            'id',
            'company',
            'contacts',
            'created_on',
            'created_by',
            'event',
            'is_event',
            'kind',
            'modified_by',
            'modified_on',
            'date',
            'dit_adviser',
            'dit_participants',
            'dit_team',
            'communication_channel',
            'grant_amount_offered',
            'investment_project',
            'net_company_receipt',
            'service',
            'service_delivery_status',
            'subject',
            'notes',
            'archived_documents_url_path',
            'policy_areas',
            'policy_feedback_notes',
            'policy_issue_types',
            'was_policy_feedback_provided',
        )
        read_only_fields = (
            'archived_documents_url_path',
        )
        validators = [
            HasAssociatedInvestmentProjectValidator(),
            ContactsBelongToCompanyValidator(),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('communication_channel', bool),
                    when=EqualsRule('kind', Interaction.KINDS.interaction),
                ),
                ValidationRule(
                    'invalid_for_non_interaction',
                    OperatorRule('investment_project', not_),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'invalid_for_service_delivery',
                    OperatorRule('communication_channel', not_),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'invalid_for_non_service_delivery',
                    OperatorRule('is_event', is_blank),
                    OperatorRule('event', is_blank),
                    OperatorRule('service_delivery_status', is_blank),
                    OperatorRule('grant_amount_offered', is_blank),
                    OperatorRule('net_company_receipt', is_blank),
                    when=EqualsRule('kind', Interaction.KINDS.interaction),
                ),
                ValidationRule(
                    'invalid_when_no_policy_feedback',
                    OperatorRule('policy_issue_types', not_),
                    OperatorRule('policy_areas', not_),
                    OperatorRule('policy_feedback_notes', not_),
                    when=OperatorRule('was_policy_feedback_provided', not_),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('policy_areas', bool),
                    OperatorRule('policy_issue_types', bool),
                    OperatorRule('policy_feedback_notes', is_not_blank),
                    when=OperatorRule('was_policy_feedback_provided', bool),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('is_event', is_not_blank),
                    when=EqualsRule('kind', Interaction.KINDS.service_delivery),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('event', bool),
                    when=OperatorRule('is_event', bool),
                ),
                ValidationRule(
                    'too_many_contacts_for_event_service_delivery',
                    OperatorRule('contacts', lambda value: len(value) <= 1),
                    when=OperatorRule('is_event', bool),
                ),
                ValidationRule(
                    'invalid_for_non_event',
                    OperatorRule('event', not_),
                    when=OperatorRule('is_event', not_),
                ),
            ),
        ]
