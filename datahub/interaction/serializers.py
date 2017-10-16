from operator import eq, not_

from django.utils.translation import ugettext_lazy
from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import is_blank, is_not_blank
from datahub.core.validators import AnyOfValidator, Condition, RulesBasedValidator, ValidationRule
from datahub.event.models import Event
from datahub.investment.models import InvestmentProject
from datahub.metadata.models import Service, Team
from .models import CommunicationChannel, Interaction


class InteractionSerializer(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    default_error_messages = {
        'invalid_for_interaction': ugettext_lazy(
            'This field cannot be specified for an interaction.'
        ),
        'invalid_for_service_delivery': ugettext_lazy(
            'This field cannot be specified for a service delivery.'
        ),
        'invalid_for_non_event': ugettext_lazy(
            'This field is only valid for event service deliveries.'
        ),
    }

    company = NestedRelatedField(Company, required=False, allow_null=True)
    contact = NestedRelatedField(Contact)
    dit_adviser = NestedAdviserField()
    created_by = NestedAdviserField(read_only=True)
    dit_team = NestedRelatedField(Team)
    communication_channel = NestedRelatedField(
        CommunicationChannel, required=False, allow_null=True
    )
    is_event = serializers.NullBooleanField(required=False)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code')
    )
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service)

    def validate(self, data):
        """
        Removes the semi-virtual field is_event from the data.

        This is removed because the value is inferred from the event field during serialisation.
        """
        if 'is_event' in data:
            del data['is_event']
        return data

    class Meta:
        model = Interaction
        extra_kwargs = {
            # Date is a datetime in the model, but only the date component is used
            # (at present). Setting the formats as below effectively makes the field
            # behave like a date field without changing the schema and breaking the
            # v1 API.
            'date': {'format': '%Y-%m-%d', 'input_formats': ['%Y-%m-%d']},
        }
        fields = (
            'id',
            'company',
            'contact',
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
            'investment_project',
            'service',
            'subject',
            'notes',
        )
        validators = [
            AnyOfValidator('company', 'investment_project'),
            RulesBasedValidator(
                ValidationRule(
                    'required', 'communication_channel', bool,
                    condition=Condition('kind', eq, (Interaction.KINDS.interaction,))
                ),
                ValidationRule(
                    'invalid_for_service_delivery', 'communication_channel', not_,
                    condition=Condition('kind', eq, (Interaction.KINDS.service_delivery,))
                ),
                ValidationRule(
                    'invalid_for_interaction', 'event', not_,
                    condition=Condition('kind', eq, (Interaction.KINDS.interaction,))
                ),
                ValidationRule(
                    'invalid_for_interaction', 'is_event', is_blank,
                    condition=Condition('kind', eq, (Interaction.KINDS.interaction,))
                ),
                ValidationRule(
                    'required', 'is_event', is_not_blank,
                    condition=Condition('kind', eq, (Interaction.KINDS.service_delivery,))
                ),
                ValidationRule(
                    'required', 'event', bool,
                    condition=Condition('is_event', bool)
                ),
                ValidationRule(
                    'invalid_for_non_event', 'event', not_,
                    condition=Condition('is_event', not_)
                ),
            )
        ]
