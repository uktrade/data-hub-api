from rest_framework import serializers

from datahub.company.serializers import NestedAdviserField
from datahub.core.serializers import NestedRelatedField
from datahub.investment.proposition.models import Proposition


class CreatePropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for create endpoint."""

    investment_project = NestedRelatedField(
        'investment.InvestmentProject',
        extra_fields=('name', 'project_code')
    )
    adviser = NestedAdviserField()

    deadline = serializers.DateField()

    name = serializers.CharField()
    scope = serializers.CharField()

    class Meta:
        model = Proposition
        fields = (
            'investment_project',
            'adviser',
            'deadline',
            'name',
            'scope',
        )


class CompletePropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for complete endpoint."""

    completed_details = serializers.CharField()

    class Meta:
        model = Proposition
        fields = (
            'completed_details',
        )

    def complete(self):
        """Complete a proposition."""
        self.instance.complete(
            by=self.context['current_user'],
            details=self.validated_data['completed_details']
        )
        return self.instance


class AbandonPropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for abandon endpoint."""

    reason_abandoned = serializers.CharField()

    class Meta:
        model = Proposition
        fields = (
            'reason_abandoned',
        )

    def abandon(self):
        """Abandon a proposition."""
        self.instance.abandon(
            by=self.context['current_user'],
            reason=self.validated_data['reason_abandoned']
        )
        return self.instance


class PropositionSerializer(serializers.ModelSerializer):
    """Proposition serialiser for view only endpoints."""

    investment_project = NestedRelatedField(
        'investment.InvestmentProject',
        extra_fields=('name', 'project_code')
    )
    adviser = NestedAdviserField()
    deadline = serializers.DateField()
    name = serializers.CharField()
    created_by = NestedAdviserField()
    abandoned_by = NestedAdviserField()
    completed_by = NestedAdviserField()

    class Meta:
        model = Proposition
        fields = (
            'id',
            'investment_project',
            'adviser',
            'deadline',
            'status',
            'name',
            'scope',
            'reason_abandoned',
            'created_on',
            'created_by',
            'abandoned_on',
            'abandoned_by',
            'completed_details',
            'completed_on',
            'completed_by',
        )
        read_only_fields = fields
