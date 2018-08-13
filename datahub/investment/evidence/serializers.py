from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.investment.evidence.models import EvidenceGroup
from datahub.investment.evidence.permissions import (
    EvidenceGroupHasAssociatedInvestmentProjectValidator
)
from datahub.investment.serializers import NestedInvestmentProjectField


class CreateEvidenceGroupSerializer(serializers.ModelSerializer):
    """Evidence Group serialiser for create endpoint."""

    class Meta:
        model = EvidenceGroup
        fields = (
            'name',
        )
        validators = (
            EvidenceGroupHasAssociatedInvestmentProjectValidator(),
        )


class EvidenceGroupSerializer(serializers.ModelSerializer):
    """Evidence Group serialiser for view only endpoints."""

    investment_project = NestedInvestmentProjectField()
    created_by = NestedAdviserField()
    modified_by = NestedAdviserField()

    class Meta:
        model = EvidenceGroup
        fields = (
            'id',
            'investment_project',
            'name',
            'created_on',
            'created_by',
            'modified_on',
            'modified_by',
        )
        read_only_fields = fields
