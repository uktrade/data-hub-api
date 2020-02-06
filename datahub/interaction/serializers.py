from collections import Counter
from operator import not_

from django.db.transaction import atomic
from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import DataCombiner, is_blank, is_not_blank
from datahub.core.validators import (
    AndRule,
    EqualsRule,
    InRule,
    IsFeatureFlagActive,
    IsObjectBeingCreated,
    NotRule,
    OperatorRule,
    RulesBasedValidator,
    ValidationRule,
)
from datahub.event.models import Event
from datahub.interaction.constants import INTERACTION_ADD_COUNTRIES
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionDITParticipant,
    InteractionExportCountry,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.permissions import HasAssociatedInvestmentProjectValidator
from datahub.interaction.validators import (
    ContactsBelongToCompanyValidator,
    DuplicateExportCountryValidator,
    ServiceAnswersValidator,
    StatusChangeValidator,
)
from datahub.investment.project.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Country, Service, Team
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


class InteractionExportCountrySerializer(serializers.ModelSerializer):
    """InteractionExportCountry serializer."""

    country = NestedRelatedField(Country)

    class Meta:
        model = InteractionExportCountry
        fields = ('country', 'status')


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
        'invalid_when_feature_flag_off': gettext_lazy(
            'export countries related fields are not valid when feature flag is off.',
        ),
        'invalid_when_no_countries_discussed': gettext_lazy(
            'This field is only valid when countries were discussed.',
        ),
        'invalid_for_update': gettext_lazy(
            'This field is invalid for interaction updates.',
        ),
    }

    INVALID_FOR_UPDATE = gettext_lazy(
        'This field is invalid for interaction updates.',
    )

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
    export_countries = InteractionExportCountrySerializer(
        allow_empty=True,
        many=True,
        required=False,
    )

    def validate_service(self, value):
        """Make sure only a service without children can be assigned."""
        if value and value.children.count() > 0:
            raise serializers.ValidationError(SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE)
        return value

    def validate_were_countries_discussed(self, were_countries_discussed):
        """
        Make sure `were_countries_discussed` field is not being updated.
        Updates are not allowed on this field.
        """
        if self.instance is None:
            return were_countries_discussed

        raise serializers.ValidationError(self.INVALID_FOR_UPDATE)

    def validate_export_countries(self, export_countries):
        """
        Make sure `export_countries` field is not being updated.
        updates are not allowed on this field.
        """
        if self.instance is None:
            return export_countries

        raise serializers.ValidationError(self.INVALID_FOR_UPDATE)

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

        Overridden to handle updating of dit_participants
        and export_countries.
        """
        dit_participants = validated_data.pop('dit_participants')
        export_countries = validated_data.pop('export_countries', [])

        interaction = super().create(validated_data)
        self._save_dit_participants(interaction, dit_participants)
        self._save_export_countries(interaction, export_countries)

        return interaction

    @atomic
    def update(self, instance, validated_data):
        """
        Create an interaction.

        Overridden to handle updating of dit_participants
        and export_countries.
        """
        dit_participants = validated_data.pop('dit_participants', None)
        export_countries = validated_data.pop('export_countries', None)
        interaction = super().update(instance, validated_data)

        # For PATCH requests, dit_participants may not be being updated
        if dit_participants is not None:
            self._save_dit_participants(interaction, dit_participants)

        if export_countries is not None:
            self._save_export_countries(interaction, export_countries)

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

    def _save_export_countries(self, interaction, validated_export_countries):
        """
        Adds export countries related to an interaction.
        Update is not allowed yet.
        An attempt to update will result in `NotImplementedError` exception.

        Syncs interaction export countries into company export countries.
        """
        existing_country_mapping = {
            export_country.country: export_country
            for export_country in interaction.export_countries.all()
        }
        new_country_mapping = {
            item['country']: item
            for item in validated_export_countries
        }

        for new_country, export_data in new_country_mapping.items():
            status = export_data['status']
            if new_country in existing_country_mapping:
                # TODO: updates are not supported yet
                raise NotImplementedError()
            InteractionExportCountry.objects.create(
                country=new_country,
                interaction=interaction,
                status=status,
                created_by=interaction.created_by,
            )
            # Sync company_CompanyExportCountry model
            # NOTE: current date is preferred over future interaction date
            current_date = now()
            record_date = current_date if interaction.date > current_date else interaction.date
            interaction.company.add_export_country(
                new_country,
                status,
                record_date,
                interaction.created_by,
            )

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
            'were_countries_discussed',
            'export_countries',
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
            DuplicateExportCountryValidator(),
            RulesBasedValidator(
                ValidationRule(
                    'required',
                    OperatorRule('communication_channel', bool),
                    when=AndRule(
                        EqualsRule('kind', Interaction.Kind.INTERACTION),
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
                    EqualsRule('kind', Interaction.Kind.INTERACTION),
                    when=EqualsRule('theme', Interaction.THEMES.investment),
                ),
                ValidationRule(
                    'invalid_for_non_interaction',
                    OperatorRule('investment_project', not_),
                    when=EqualsRule('kind', Interaction.Kind.SERVICE_DELIVERY),
                ),
                ValidationRule(
                    'invalid_for_service_delivery',
                    OperatorRule('communication_channel', not_),
                    when=EqualsRule('kind', Interaction.Kind.SERVICE_DELIVERY),
                ),
                ValidationRule(
                    'invalid_for_non_service_delivery',
                    OperatorRule('is_event', is_blank),
                    OperatorRule('event', is_blank),
                    OperatorRule('service_delivery_status', is_blank),
                    when=EqualsRule('kind', Interaction.Kind.INTERACTION),
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
                    when=EqualsRule('kind', Interaction.Kind.SERVICE_DELIVERY),
                ),
                ValidationRule(
                    'too_many_contacts_for_event_service_delivery',
                    OperatorRule('contacts', lambda value: len(value) <= 1),
                    when=OperatorRule('is_event', bool),
                ),
                ValidationRule(
                    'invalid_when_feature_flag_off',
                    OperatorRule('were_countries_discussed', is_blank),
                    OperatorRule('export_countries', is_blank),
                    when=AndRule(
                        IsObjectBeingCreated(),
                        NotRule(IsFeatureFlagActive(INTERACTION_ADD_COUNTRIES)),
                    ),
                ),
                ValidationRule(
                    'invalid_for_investment',
                    OperatorRule('were_countries_discussed', not_),
                    OperatorRule('export_countries', not_),
                    when=EqualsRule('theme', Interaction.THEMES.investment),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('were_countries_discussed', is_not_blank),
                    when=AndRule(
                        IsObjectBeingCreated(),
                        IsFeatureFlagActive(INTERACTION_ADD_COUNTRIES),
                        InRule(
                            'theme',
                            [Interaction.THEMES.export, Interaction.THEMES.other],
                        ),
                    ),
                ),
                ValidationRule(
                    'required',
                    OperatorRule('export_countries', is_not_blank),
                    when=AndRule(
                        OperatorRule('were_countries_discussed', bool),
                        InRule(
                            'theme',
                            [Interaction.THEMES.export, Interaction.THEMES.other],
                        ),
                    ),
                ),
                ValidationRule(
                    'invalid_when_no_countries_discussed',
                    OperatorRule('export_countries', is_blank),
                    when=AndRule(
                        IsObjectBeingCreated(),
                        IsFeatureFlagActive(INTERACTION_ADD_COUNTRIES),
                        OperatorRule('were_countries_discussed', not_),
                        InRule(
                            'theme',
                            [Interaction.THEMES.export, Interaction.THEMES.other],
                        ),
                    ),
                ),
                # These two rules are only checked for service deliveries as there's a separate
                # check that event is blank for interactions above which takes precedence (to
                # avoid duplicate or contradictory error messages)
                ValidationRule(
                    'required',
                    OperatorRule('event', bool),
                    when=AndRule(
                        OperatorRule('is_event', bool),
                        EqualsRule('kind', Interaction.Kind.SERVICE_DELIVERY),
                    ),
                ),
                ValidationRule(
                    'invalid_for_non_event',
                    OperatorRule('event', not_),
                    when=AndRule(
                        OperatorRule('is_event', not_),
                        EqualsRule('kind', Interaction.Kind.SERVICE_DELIVERY),
                    ),
                ),
            ),
        ]
