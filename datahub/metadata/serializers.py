from functools import partial

from django.utils.translation import gettext_lazy
from rest_framework import serializers

from datahub.core.serializers import ConstantModelSerializer, NestedRelatedField
from datahub.interaction.models import ServiceAnswerOption, ServiceQuestion
from datahub.metadata.models import Country, OverseasRegion, Service, TeamRole, UKRegion


SERVICE_LEAF_NODE_NOT_SELECTED_MESSAGE = gettext_lazy(
    'This field is valid for services without children services.',
)


TeamWithGeographyField = partial(
    NestedRelatedField,
    'metadata.Team',
    extra_fields=(
        'name',
        ('uk_region', NestedRelatedField(UKRegion, read_only=True)),
        ('country', NestedRelatedField(Country, read_only=True)),
    ),
)


class AdministrativeAreaSerializer(ConstantModelSerializer):
    """Administrative area serializer."""

    country = NestedRelatedField(Country, read_only=True)
    area_code = serializers.ReadOnlyField()


class CountrySerializer(ConstantModelSerializer):
    """Country serializer."""

    overseas_region = NestedRelatedField(OverseasRegion, read_only=True)
    iso_alpha2_code = serializers.ReadOnlyField()


class ServiceAnswerOptionSerializer(serializers.ModelSerializer):
    """Serializer for service answer options (used in ServiceQuestionSerializer)."""

    class Meta:
        model = ServiceAnswerOption
        fields = (
            'disabled_on',
            'id',
            'name',
        )
        read_only_fields = fields


class ServiceQuestionSerializer(serializers.ModelSerializer):
    """Serializer for service questions (used in ServiceSerializer)."""

    answer_options = ServiceAnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceQuestion
        fields = (
            'disabled_on',
            'id',
            'name',
            'answer_options',
        )
        read_only_fields = fields


class ServiceSerializer(ConstantModelSerializer):
    """Service serializer."""

    contexts = serializers.MultipleChoiceField(choices=Service.Context.choices, read_only=True)
    interaction_questions = ServiceQuestionSerializer(many=True, read_only=True)


class TeamSerializer(ConstantModelSerializer):
    """Team serializer."""

    role = NestedRelatedField(TeamRole, read_only=True)
    uk_region = NestedRelatedField(UKRegion, read_only=True)
    country = NestedRelatedField(Country, read_only=True)


class SectorSerializer(serializers.Serializer):
    """Sector serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    segment = serializers.ReadOnlyField()
    parent = NestedRelatedField('metadata.Sector', read_only=True)
    level = serializers.ReadOnlyField()
    disabled_on = serializers.ReadOnlyField()


class InvestmentProjectStageSerializer(ConstantModelSerializer):
    """Investment project stage serializer."""

    exclude_from_investment_flow = serializers.ReadOnlyField()
