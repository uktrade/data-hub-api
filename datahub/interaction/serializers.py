from collections import Counter
from operator import not_

from django.db.transaction import atomic
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank
from datahub.core.validators import (
    AndRule,
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
from datahub.interaction.validators import (
    ContactsBelongToCompanyValidator,
    ServiceAnswersValidator,
    StatusChangeValidator,
)
from datahub.investment.project.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Service, Team
from datahub.metadata.serializers import SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE


class InteractionDITParticipantListSerializer(serializers.ListSerializer):
    """Interaction DIT participant list serialiser that adds validation for duplicates."""

    default_error_messages = {
        'duplicate_adviser': gettext_lazy(
            'You cannot add the same adviser more than once.',
        ),
    }

    def run_validation(self, data=serializers.empty):
        """
        Validates that there are no duplicate advisers.

        Unfortunately, overriding validate() results in a error dict being returned and the errors
        being placed in non_field_errors. Hence, run_validation() is overridden instead (to get
        the expected behaviour of an error list being returned, with each entry corresponding
        to each item in the request body).
        """
        value = super().run_validation(data)
        counts = Counter(dit_participant['adviser'] for dit_participant in value)

        if len(counts) == len(value):
            return value

        errors = []
        for item in value:
            item_errors = {}

            if counts[item['adviser']] > 1:
                item_errors['adviser'] = [self.error_messages['duplicate_adviser']]

            errors.append(item_errors)

        raise serializers.ValidationError(errors)


class InteractionDITParticipantSerializer(serializers.ModelSerializer):
    """
    Interaction DIT participant serialiser.

    Used as a field in InteractionSerializer.
    """

    adviser = NestedAdviserField()
    # team is read-only as it is set from the adviser when a participant is added to
    # an interaction
    team = NestedRelatedField(Team, read_only=True)

    @classmethod
    def many_init(cls, *args, **kwargs):
        """Initialises a many=True instance of the serialiser with a custom list serialiser."""
        child = cls(context=kwargs.get('context'))
        return InteractionDITParticipantListSerializer(child=child, *args, **kwargs)

    class Meta:
        model = InteractionDITParticipant
        fields = ('adviser', 'team')
        # Explicitly set validator as extra protection against a unique together validator being
        # added.
        # (UniqueTogetherValidator would not function correctly when multiple items are being
        # updated at once.)
        validators = []


class InteractionSerializer(serializers.ModelSerializer):
    """
    Interaction serialiser.

    Note that interactions can also be created and/or modified by:

    - the standard admin site functionality
    - the import interactions tool in the admin site
    - the calendar meeting invite processing tool

    If you're making changes to interaction functionality you should consider if any changes
    are required to the functionality listed above as well.

    Also note that the import interactions tool also uses the validators from this class,
    the calendar meeting invite processing tool uses the serializer as a whole to
    create interactions.
    """

    default_error_messages = {
        'invalid_for_investment': gettext_lazy(
            "This value can't be selected for investment interactions.",
        ),
        'invalid_for_non_service_delivery': gettext_lazy(
            'This field is only valid for service deliveries.',
        ),
        'invalid_for_service_delivery': gettext_lazy(
            'This field is not valid for service deliveries.',
        ),
        'invalid_for_non_interaction': gettext_lazy(
            'This field is only valid for interactions.',
        ),
        'invalid_for_non_interaction_or_service_delivery': gettext_lazy(
            'This value is only valid for interactions and service deliveries.',
        ),
        'invalid_for_non_event': gettext_lazy(
            'This field is only valid for event service deliveries.',
        ),
        'invalid_when_no_policy_feedback': gettext_lazy(
            'This field is only valid when policy feedback has been provided.',
        ),
        'too_many_contacts_for_event_service_delivery': gettext_lazy(
            'Only one contact can be provided for event service deliveries.',
        ),
        'cannot_unset_theme': gettext_lazy(
            "A theme can't be removed once set.",
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
    archived_by = NestedAdviserField(read_only=True)
    dit_participants = InteractionDITParticipantSerializer(
        many=True,
        allow_empty=False,
    )
    communication_channel = NestedRelatedField(
        CommunicationChannel, required=False, allow_null=True,
    )
    is_event = serializers.BooleanField(required=False, allow_null=True)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedInvestmentProjectField(required=False, allow_null=True)
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service, required=False, allow_null=True)
    service_answers = serializers.JSONField(required=False)
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

    def validate_service(self, value):
        """Make sure only a service without children can be assigned."""
        if value and value.children.count() > 0:
            raise serializers.ValidationError(SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE)
        return value

    def validate(self, data):
        """
        Validates and cleans the data.

        This removes the semi-virtual field is_event from the data.

        This is removed because the value is not stored; it is instead inferred from contents
        of the the event field during serialisation.
        """
        self._validate_theme(data)

        if 'is_event' in data:
            del data['is_event']

        # Ensure that archived=False is set for creations/updates, when the
        # existing instance does not have a value for it
        # TODO: remove this once we give archived a model-level default
        if not self.instance or self.instance.archived is None:
            data['archived'] = False

        return data

    @atomic
    def create(self, validated_data):
        """
        Create an interaction.

        Overridden to handle updating of dit_participants.
        """
        dit_participants = validated_data.pop('dit_participants')

        interaction = super().create(validated_data)
        self._save_dit_participants(interaction, dit_participants)

        return interaction

    @atomic
    def update(self, instance, validated_data):
        """
        Create an interaction.

        Overridden to handle updating of dit_participants.
        """
        dit_participants = validated_data.pop('dit_participants', None)
        interaction = super().update(instance, validated_data)

        # For PATCH requests, dit_participants may not be being updated
        if dit_participants is not None:
            self._save_dit_participants(interaction, dit_participants)

        return interaction

    def _validate_theme(self, data):
        """Make sure that a theme is not unset once it has been set for an interaction."""
        combiner = DataCombiner(self.instance, data)
        if self.instance and self.instance.theme and not combiner.get_value('theme'):
            error = {
                'theme': [
                    self.error_messages['cannot_unset_theme'],
                ],
            }
            raise serializers.ValidationError(error, code='cannot_unset_theme')

    def _save_dit_participants(self, interaction, validated_dit_participants):
        """
        Updates the DIT participants for an interaction.

        This compares the provided list of participants with the current list, and adds and
        removes participants as necessary.

        This is based on example code in DRF documentation for ListSerializer.

        Note that adviser's team is also saved in the participant when a participant is added
        to an interaction, so that if the adviser later moves team, the interaction is still
        recorded against the original team.
        """
        old_adviser_mapping = {
            dit_participant.adviser: dit_participant
            for dit_participant in interaction.dit_participants.all()
        }
        old_advisers = old_adviser_mapping.keys()
        new_advisers = {
            dit_participant['adviser'] for dit_participant in validated_dit_participants
        }

        # Create new DIT participants
        for adviser in new_advisers - old_advisers:
            InteractionDITParticipant(
                adviser=adviser,
                interaction=interaction,
                team=adviser.dit_team,
            ).save()

        # Delete removed DIT participants
        for adviser in old_advisers - new_advisers:
            old_adviser_mapping[adviser].delete()

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
            'status': {'default': Interaction.STATUSES.complete},
            'theme': {
                'allow_blank': False,
                'default': None,
            },
        }
        fields = (
            'id',
            'company',
            'contacts',
            'created_on',
            'created_by',
            'event',
            'is_event',
            'status',
            'kind',
            'modified_by',
            'modified_on',
            'date',
            'dit_participants',
            'communication_channel',
            'grant_amount_offered',
            'investment_project',
            'net_company_receipt',
            'service',
            'service_answers',
            'service_delivery_status',
            'subject',
            'theme',
            'notes',
            'archived_documents_url_path',
            'policy_areas',
            'policy_feedback_notes',
            'policy_issue_types',
            'was_policy_feedback_provided',
            'archived',
            'archived_by',
            'archived_on',
            'archived_reason',
        )
        read_only_fields = (
            'archived_documents_url_path',
            'archived',
            'archived_by',
            'archived_on',
            'archived_reason',
        )
        # Note: These validators are also used by the admin site import interactions tool
        # (see the admin_csv_import sub-package)
        validators = [
            HasAssociatedInvestmentProjectValidator(),
            ContactsBelongToCompanyValidator(),
            StatusChangeValidator(),
            ServiceAnswersValidator(),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('communication_channel', bool),
                    when=AndRule(
                        EqualsRule('kind', Interaction.KINDS.interaction),
                        EqualsRule('status', Interaction.STATUSES.complete),
                    ),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('service', bool),
                    when=EqualsRule('status', Interaction.STATUSES.complete),
                ),
                ValidationRule(
                    'invalid_for_investment',
                    EqualsRule('kind', Interaction.KINDS.interaction),
                    when=EqualsRule('theme', Interaction.THEMES.investment),
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
                    'too_many_contacts_for_event_service_delivery',
                    OperatorRule('contacts', lambda value: len(value) <= 1),
                    when=OperatorRule('is_event', bool),
                ),
                # These two rules are only checked for service deliveries as there's a separate
                # check that event is blank for interactions above which takes precedence (to
                # avoid duplicate or contradictory error messages)
                ValidationRule(
                    'required',
                    OperatorRule('event', bool),
                    when=AndRule(
                        OperatorRule('is_event', bool),
                        EqualsRule('kind', Interaction.KINDS.service_delivery),
                    ),
                ),
                ValidationRule(
                    'invalid_for_non_event',
                    OperatorRule('event', not_),
                    when=AndRule(
                        OperatorRule('is_event', not_),
                        EqualsRule('kind', Interaction.KINDS.service_delivery),
                    ),
                ),
            ),
        ]
