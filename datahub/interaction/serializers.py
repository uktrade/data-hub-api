from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import AdviserSerializer, NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import AnyOfValidator, DataCombiner, RequiredUnlessAlreadyBlank
from datahub.event.models import Event
from datahub.investment.models import InvestmentProject
from datahub.metadata.models import InteractionType, Service, Team
from .models import Interaction


class InteractionSerializerReadV1(serializers.ModelSerializer):
    """Interaction Serializer."""

    dit_adviser = AdviserSerializer()

    class Meta:  # noqa: D101
        model = Interaction
        depth = 2
        fields = '__all__'


class InteractionSerializerWriteV1(serializers.ModelSerializer):
    """Interaction Serializer for writing operations."""

    class Meta:  # noqa: D101
        model = Interaction
        fields = '__all__'
        extra_kwargs = {
            # Temporarily set a default for kind for backwards compatibility
            'kind': {'default': Interaction.KINDS.interaction},
        }
        validators = [
            AnyOfValidator('company', 'investment_project'),
            RequiredUnlessAlreadyBlank('dit_team', 'communication_channel', 'service')
        ]


class InteractionSerializerV3(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    company = NestedRelatedField(Company, required=False, allow_null=True)
    contact = NestedRelatedField(Contact, required=False, allow_null=True)
    dit_adviser = NestedAdviserField()
    created_by = NestedAdviserField(read_only=True)
    dit_team = NestedRelatedField(Team)
    communication_channel = NestedRelatedField(InteractionType, required=False, allow_null=True)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code')
    )
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service)
    # Added for backwards compatibility. Will be removed once the front end is updated.
    interaction_type = NestedRelatedField(
        InteractionType,
        source='communication_channel',
        required=False,
        allow_null=True
    )

    def validate(self, data):
        """
        Perform cross-field validation.

        Called by DRF.
        """
        combiner = DataCombiner(instance=self.instance, update_data=data)
        is_interaction = combiner.get_value('kind') == Interaction.KINDS.interaction

        if is_interaction and not combiner.get_value('communication_channel'):
            raise serializers.ValidationError({
                'communication_channel': self.error_messages['required']
            })

        return data

    class Meta:  # noqa: D101
        model = Interaction
        extra_kwargs = {
            # Date is a datetime in the model, but only the date component is used
            # (at present). Setting the formats as below effectively makes the field
            # behave like a date field without changing the schema and breaking the
            # v1 API.
            'date': {'format': '%Y-%m-%d', 'input_formats': ['%Y-%m-%d']},
            # Temporarily set a default for kind for backwards compatibility
            'kind': {'default': Interaction.KINDS.interaction},
        }
        fields = (
            'id',
            'company',
            'contact',
            'created_on',
            'created_by',
            'event',
            'kind',
            'modified_by',
            'modified_on',
            'date',
            'dit_adviser',
            'dit_team',
            'communication_channel',
            'interaction_type',
            'investment_project',
            'service',
            'subject',
            'notes',
        )
        validators = [
            AnyOfValidator('company', 'investment_project'),
        ]
