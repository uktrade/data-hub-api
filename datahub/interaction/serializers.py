from rest_framework import serializers

from datahub.company.models import Company, Contact
from datahub.company.serializers import AdviserSerializer, NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.core.validate_utils import AnyOfValidator, RequiredUnlessAlreadyBlank
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
        validators = [
            AnyOfValidator('company', 'investment_project'),
            RequiredUnlessAlreadyBlank('dit_team', 'interaction_type', 'service')
        ]


class InteractionSerializerV3(serializers.ModelSerializer):
    """V3 interaction serialiser."""

    company = NestedRelatedField(Company, required=False, allow_null=True)
    contact = NestedRelatedField(Contact, required=False, allow_null=True)
    dit_adviser = NestedAdviserField()
    dit_team = NestedRelatedField(Team)
    interaction_type = NestedRelatedField(InteractionType)
    investment_project = NestedRelatedField(
        InvestmentProject, required=False, allow_null=True, extra_fields=('name', 'project_code')
    )
    service = NestedRelatedField(Service)

    class Meta:  # noqa: D101
        model = Interaction
        extra_kwargs = {
            # Date is a datetime in the model, but only the date component is used
            # (at present). This effectively makes it behave like a date field without
            # changing the schema and breaking the v1 API.
            'date': {'format': '%Y-%m-%d', 'input_formats': ['%Y-%m-%d']}
        }
        fields = (
            'id',
            'company',
            'contact',
            'created_on',
            'created_by',
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
