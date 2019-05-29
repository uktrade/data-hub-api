from collections import Counter
from operator import not_

from django.db.transaction import atomic
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank
from datahub.core.validators import (
    AllIsBlankRule,
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
    StatusChangeValidator,
)
from datahub.investment.project.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Service, Team


class InteractionDITParticipantListSerializer(serializers.ListSerializer):
    """Interaction DIT participant list serialiser that adds validation for duplicates."""

    default_error_messages = {
        'duplicate_adviser': gettext_lazy(
            'You cannot add the same adviser more than once.',
        ),
    }

    def bind(self, field_name, parent):
        """
        Overridden to set self.partial to False as otherwise allow_empty=False does not behave
        correctly.

        See https://github.com/encode/django-rest-framework/issues/6509.
        """
        super().bind(field_name, parent)
        self.partial = False

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
        'one_participant_field': gettext_lazy(
            'If dit_participants is provided, dit_adviser and dit_team must be omitted.',
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
    # dit_adviser has been replaced by dit_participants but is retained for temporary backwards
    # compatibility
    # TODO: Remove following deprecation period
    dit_adviser = NestedAdviserField(required=False)
    # TODO: Remove required=False once dit_adviser and dit_team have been removed
    dit_participants = InteractionDITParticipantSerializer(
        many=True,
        allow_empty=False,
        required=False,
    )
    # dit_team has been replaced by dit_participants but is retained for temporary backwards
    # compatibility
    # TODO: Remove following deprecation period
    dit_team = NestedRelatedField(Team, required=False)
    communication_channel = NestedRelatedField(
        CommunicationChannel, required=False, allow_null=True,
    )
    is_event = serializers.BooleanField(required=False, allow_null=True)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedInvestmentProjectField(required=False, allow_null=True)
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service, required=False, allow_null=True)
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
        Validates and cleans the data.

        This removes the semi-virtual field is_event from the data.

        This is removed because the value is not stored; it is instead inferred from contents
        of the the event field during serialisation.

        It also:
          - checks that if `dit_participants` has been provided, `dit_adviser` or `dit_team`
          haven't also been provided
          - copies the first value in `contacts` to `contact`
          - copies the first value in `dit_participants` to `dit_adviser` and `dit_team`
        """
        self._validate_theme(data)

        has_dit_adviser_or_dit_team = {'dit_adviser', 'dit_team'} & data.keys()
        has_dit_participants = 'dit_participants' in data

        if has_dit_adviser_or_dit_team and has_dit_participants:
            error = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    self.error_messages['one_participant_field'],
                ],
            }
            raise serializers.ValidationError(error, code='one_participant_field')

        if 'is_event' in data:
            del data['is_event']

        # If dit_participants has been provided, this copies the first participant to
        # dit_adviser and dit_team (for backwards compatibility).
        # TODO Remove once dit_adviser and dit_team removed from the database.
        if 'dit_participants' in data:
            first_participant = data['dit_participants'][0]
            data['dit_adviser'] = first_participant['adviser']
            data['dit_team'] = first_participant['adviser'].dit_team

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
        return self._create_or_update(validated_data)

    @atomic
    def update(self, instance, validated_data):
        """
        Create an interaction.

        Overridden to handle updating of dit_participants.
        """
        return self._create_or_update(validated_data, instance=instance, is_update=True)

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

    def _create_or_update(self, validated_data, instance=None, is_update=False):
        dit_participants = validated_data.pop('dit_participants', None)

        if is_update:
            interaction = super().update(instance, validated_data)
        else:
            interaction = super().create(validated_data)

        # If dit_participants has not been provided, create, update and remove participants using
        # the provided dit_adviser and dit_team values
        # TODO: Remove the 'if dit_participants is None' part once dit_adviser and dit_team have
        #  been removed from the API.
        if dit_participants is None:
            InteractionDITParticipant.objects.update_or_create(
                interaction=interaction,
                adviser=interaction.dit_adviser,
                defaults={
                    'team': interaction.dit_team,
                },
            )

            InteractionDITParticipant.objects.filter(
                interaction=interaction,
            ).exclude(
                adviser=interaction.dit_adviser,
            ).delete()
        else:
            self._save_dit_participants(interaction, dit_participants)

        return interaction

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
            'theme',
            'notes',
            'archived_documents_url_path',
            'policy_areas',
            'policy_feedback_notes',
            'policy_issue_types',
            'was_policy_feedback_provided',
            'location',
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
            RulesBasedValidator(
                # If dit_adviser and dit_team are *omitted* (note that they already have
                # allow_null=False) we assume that dit_participants is being used, and return an
                # error if it is empty.
                # TODO: Remove once dit_adviser and dit_team have been removed.
                ValidationRule(
                    'required',
                    OperatorRule('dit_participants', bool),
                    when=AllIsBlankRule('dit_adviser', 'dit_team'),
                ),
                # If dit_adviser has been provided, double-check that dit_team is also set.
                # TODO: Remove once dit_adviser and dit_team have been removed.
                ValidationRule(
                    'required',
                    OperatorRule('dit_adviser', bool),
                    when=AndRule(
                        OperatorRule('dit_team', bool),
                        OperatorRule('dit_participants', not_),
                    ),
                ),
                # If dit_team has been provided, double-check that dit_adviser is also set.
                # TODO: Remove once dit_adviser and dit_team have been removed.
                ValidationRule(
                    'required',
                    OperatorRule('dit_team', bool),
                    when=AndRule(
                        OperatorRule('dit_adviser', bool),
                        OperatorRule('dit_participants', not_),
                    ),
                ),
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
