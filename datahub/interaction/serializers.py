from operator import not_

from django.utils.translation import ugettext_lazy
from rest_framework import serializers
from rest_framework.settings import api_settings

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
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.permissions import HasAssociatedInvestmentProjectValidator
from datahub.interaction.validators import ContactsBelongToCompanyValidator
from datahub.investment.serializers import NestedInvestmentProjectField
from datahub.metadata.models import Service, Team


class _ManyRelatedAsSingleItemField(NestedRelatedField):
    """
    Serialiser field that makes a to-many field behave like a to-one field.

    Use for temporary backwards compatibility when migrating a to-one field to be a to-many field
    (so that a to-one field can be emulated using a to-many field).

    This isn't intended to be used in any other way as if the to-many field contains multiple
    items, only one of them will be returned, and all of them will overwritten on updates.

    TODO Remove this once contact has been removed from interactions.
    """

    def run_validation(self, data=serializers.empty):
        """Validate a user-provided value and return the internal value (converted to a list)."""
        validated_value = super().run_validation(data)
        return [validated_value] if validated_value else []

    def to_representation(self, value):
        """Converts a query set to a dict representation of the first item in the query set."""
        if not value.exists():
            return None

        return super().to_representation(value.first())


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
        'one_contact_field': ugettext_lazy(
            'Only one of contact and contacts should be provided.',
        ),
    }

    company = NestedRelatedField(Company)
    # TODO Remove contact following deprecation period
    contact = _ManyRelatedAsSingleItemField(
        Contact,
        extra_fields=(
            'name',
            'first_name',
            'last_name',
            'job_title',
        ),
        source='contacts',
        required=False,
    )
    # TODO Make required once contact has been removed
    contacts = NestedRelatedField(
        Contact,
        many=True,
        extra_fields=(
            'name',
            'first_name',
            'last_name',
            'job_title',
        ),
        required=False,
    )
    dit_adviser = NestedAdviserField()
    created_by = NestedAdviserField(read_only=True)
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

    def to_internal_value(self, data):
        """
        Checks that contact and contacts haven't both been provided.

        Note: On serialisers, to_internal_value() is called before validate().

        TODO Remove once contact removed from the API.
        """
        if 'contact' in data and 'contacts' in data:
            error = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    self.error_messages['one_contact_field'],
                ],
            }
            raise serializers.ValidationError(error, code='one_contact_field')

        return super().to_internal_value(data)

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
            # TODO Remove contact following deprecation period
            'contact',
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
                # Because contacts could come from either contact or contacts, this has to be at
                # the object level
                # TODO Remove once contact has been removed and required=False removed from
                #  contacts
                ValidationRule(
                    'required',
                    OperatorRule('contacts', bool),
                ),
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
                    'invalid_for_non_event',
                    OperatorRule('event', not_),
                    when=OperatorRule('is_event', not_),
                ),
            ),
        ]
