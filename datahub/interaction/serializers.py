from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import AdviserSerializer, NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import AnyOfValidator, RequiredUnlessAlreadyBlank
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
            RequiredUnlessAlreadyBlank('dit_team', 'interaction_type', 'service')
        ]


class InteractionSerializerV3(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    company = NestedRelatedField(Company, required=False, allow_null=True)
    contact = NestedRelatedField(Contact, required=False, allow_null=True)
    dit_adviser = NestedAdviserField()
    created_by = NestedAdviserField(read_only=True)
    dit_team = NestedRelatedField(Team)
    interaction_type = NestedRelatedField(InteractionType)
    event = NestedRelatedField(Event, required=False, allow_null=True)
    investment_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code')
    )
    modified_by = NestedAdviserField(read_only=True)
    service = NestedRelatedField(Service)

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
            'interaction_type',
            'investment_project',
            'service',
            'subject',
            'notes',
        )
        validators = [
            AnyOfValidator('company', 'investment_project'),
        ]
